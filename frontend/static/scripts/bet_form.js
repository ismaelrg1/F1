function getCSRFToken() {
    return document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_access_token='))
        ?.split('=')[1];
}

async function handleBetFormSubmit(event, betType, raceName, raceId) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // 🔍 Recorrer todos los campos del formulario y asegurarse de que existen en `data`
    form.querySelectorAll("input, select").forEach(input => {
        data[input.name] = input.value.trim(); // Guardar el valor, aunque esté vacío
    });

    // 🔍 Verificar si todos los campos están llenos
    let emptyFields = [];
    for (let [key, value] of Object.entries(data)) {
        if (!value.trim()) {
            emptyFields.push(key);
        }
    }

    if (emptyFields.length > 0) {
        alert("Por favor, completa todos los campos antes de enviar.");

        // 🛑 Resaltar los campos vacíos
        emptyFields.forEach(field => {
            let inputField = form.querySelector(`[name="${field}"]`);
            if (inputField) {
                inputField.style.border = "2px solid red";
                setTimeout(() => inputField.style.border = "", 3000); // 🔄 Quitar resaltado después de 3s
            }
        });

        return; // ❌ No enviar la apuesta si hay campos vacíos
    }

    try {
        // Aplicar power-up pendiente antes del primer envio
        const pendingKey = window.__powerupPendingKey;
        if (pendingKey) {
            const pending = JSON.parse(localStorage.getItem(pendingKey) || "null");
            if (pending && pending.race === raceName) {
                const confirmUse = confirm("¿Quieres aplicar el power-up seleccionado en este GP? Esta acción no se puede deshacer.");
                if (confirmUse) {
                    const resPower = await fetch("/api/powerups/use", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRF-TOKEN": getCSRFToken()
                        },
                        credentials: "include",
                        body: JSON.stringify(pending)
                    });
                    const powerText = await resPower.text();
                    const powerJson = JSON.parse(powerText || "{}");
                    if (!resPower.ok) {
                        alert(powerJson.error || powerJson.message || "Error al aplicar power-up.");
                        return;
                    }
                    localStorage.removeItem(pendingKey);
                }
            }
        }

        const response = await fetch(`/api/set-bet`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCSRFToken() // Include CSRF token for security
            },
            credentials: 'include', // Include authentication cookies
            body: JSON.stringify({
                ...data,
                type: betType,
                race: raceName,
                id: raceId
            })
        });

        const textResponse = await response.text();
        console.log("🔍 Server Response (raw):", textResponse);

        const jsonResponse = JSON.parse(textResponse);
        if (response.ok) {
            alert("Apuesta enviada correctamente");

            // Change button text to "Modify"
            const submitButton = form.querySelector("button[type='submit']");
            if (submitButton) {
                submitButton.textContent = "Modificar";
            }
        } else {
            alert("Error: " + jsonResponse.error);
        }
    } catch (error) {
        console.error("❌ Error sending bet:", error);
        alert("Hubo un problema al enviar la apuesta");
    }
}

// window.addEventListener("load", async () => {
//     try {
//         const raceName = "{{ race_event.event_name }}";
//         const raceYear = "{{ race_event.year }}";
//
//         const response = await fetch(`/api/race/${raceName}-${raceYear}`, {
//             method: 'GET',
//             credentials: 'include'
//         });
//
//         if (response.ok) {
//             const updatedData = await response.json();
//             console.log("🔄 Datos actualizados:", updatedData);
//
//             // 🔹 Aquí puedes actualizar los elementos HTML con los nuevos datos
//             document.getElementById("race-title").textContent = updatedData.event_name;
//             document.getElementById("race-format").textContent = `Formato: ${updatedData.event_format}`;
//
//             // Puedes iterar sobre los bets y actualizar la interfaz
//         } else {
//             console.error("⚠️ Error al obtener los datos actualizados");
//         }
//     } catch (error) {
//         console.error("❌ Error en la actualización:", error);
//     }
// });
