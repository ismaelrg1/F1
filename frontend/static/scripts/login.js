async function login(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    console.log(window.location.hostname)

    try {
        const response = await fetch(`https://${window.location.hostname}:5000/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'  // Asegura que las cookies se envíen con la solicitud
        });

        if (response.ok) {
            window.location.href = '/home';  // Redirige a la página protegida
        } else {
            const error = await response.json();
            alert(error.msg);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Something went wrong. Please try again.');
    }
}

async function register() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    if (!username || !password) {
        alert("Por favor, completa todos los campos.");
        return;
    }

    const response = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (response.ok) {
        alert("Usuario registrado con éxito. Ahora puedes iniciar sesión.");
    } else {
        alert("Error: " + data.msg);
    }
}