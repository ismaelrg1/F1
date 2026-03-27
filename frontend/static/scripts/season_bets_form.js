function getCSRFToken() {
    return document.cookie
        .split(";")
        .map(row => row.trim())
        .find(row => row.startsWith("csrf_access_token="))
        ?.split("=")[1];
}

async function submitSeasonBets(event) {
    event.preventDefault();

    const form = event.target;
    const payload = { bets: {} };

    // Validar campos vacíos
    let emptyFields = [];

    // Radios: validar por grupo
    const radioNames = new Set();
    form.querySelectorAll("input[type=radio][data-bet-id]").forEach(r => {
        radioNames.add(r.name);
    });
    radioNames.forEach(name => {
        if (!form.querySelector(`input[name="${name}"]:checked`)) {
            emptyFields.push(name);
        }
    });

    // Resto de inputs
    form.querySelectorAll("[data-bet-id]").forEach((el) => {
        if (el.type === "radio") return;
        if (!el.value.trim()) {
            emptyFields.push(el.name);
        }
    });

    if (emptyFields.length > 0) {
        alert("Por favor, completa todos los campos antes de enviar.");

        emptyFields.forEach(field => {
            const inputField = form.querySelector(`[name="${field}"]`);
            if (inputField) {
                inputField.style.border = "2px solid red";
                setTimeout(() => inputField.style.border = "", 3000);
            }
        });

        return;
    }

    // Construir payload
    form.querySelectorAll("[data-bet-id]").forEach((el) => {
        const betId = el.getAttribute("data-bet-id");
        if (!betId) return;

        if (el.type === "radio") {
            if (!el.checked) return;
            payload.bets[betId] = el.value.trim();
        } else {
            payload.bets[betId] = el.value.trim();
        }
    });

    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-TOKEN": getCSRFToken()
            },
            body: JSON.stringify(payload),
            credentials: "include"
        });

        const data = await response.json();

        if (response.ok) {
            window.location.reload();
        } else {
            alert(data.msg || "Error al guardar.");
        }
    } catch (err) {
        console.error(err);
        alert("Error inesperado");
    }
}
