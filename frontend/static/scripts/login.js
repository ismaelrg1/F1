async function login(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('http://127.0.0.1:5000/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'  // Asegura que las cookies se envíen con la solicitud
        });

        if (response.ok) {
            window.location.href = '/calendario';  // Redirige a la página protegida
        } else {
            const error = await response.json();
            alert(error.msg);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Something went wrong. Please try again.');
    }
}