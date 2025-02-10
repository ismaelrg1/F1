document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("theme-toggle");
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");

    function setThemeIcon(isDark) {
        toggleButton.innerHTML = isDark ? "☀️" : "🌙"; // Ahora usa iconos visibles
    }

    // Verificar si hay un tema guardado en localStorage
    let storedTheme = localStorage.getItem("theme");

    if (storedTheme) {
        document.documentElement.setAttribute("data-theme", storedTheme);
        setThemeIcon(storedTheme === "dark");
    } else {
        // Aplicar automáticamente el tema del sistema si no hay tema guardado
        if (prefersDarkScheme.matches) {
            document.documentElement.setAttribute("data-theme", "dark");
            localStorage.setItem("theme", "dark");
            setThemeIcon(true);
        } else {
            document.documentElement.setAttribute("data-theme", "light");
            localStorage.setItem("theme", "light");
            setThemeIcon(false);
        }
    }

    // Alternar manualmente el tema
    toggleButton.addEventListener("click", function () {
        let currentTheme = document.documentElement.getAttribute("data-theme");

        if (currentTheme === "dark") {
            document.documentElement.setAttribute("data-theme", "light");
            localStorage.setItem("theme", "light");
            setThemeIcon(false);
        } else {
            document.documentElement.setAttribute("data-theme", "dark");
            localStorage.setItem("theme", "dark");
            setThemeIcon(true);
        }
    });
});
