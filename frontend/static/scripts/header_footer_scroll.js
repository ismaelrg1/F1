(function() {
    let lastScrollTop = 0;
    const header = document.querySelector('header');
    const footer = document.querySelector('footer');

    function checkFooterVisibility() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const documentHeight = document.documentElement.scrollHeight;
        const windowHeight = window.innerHeight;
        const scrolledPercentage = (scrollTop + windowHeight) / documentHeight * 100;

        if (scrolledPercentage >= 80 || documentHeight <= windowHeight) {
            // Mostrar footer si has llegado al 80% o no hay scroll
            footer.style.bottom = "0";
        } else {
            footer.style.bottom = "-70px";
        }
    }

    window.addEventListener('scroll', function () {
        if (window.ignoreScroll) {
            // 🚫 Si estamos en scroll automático, no hacemos nada
            return;
        }

        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > lastScrollTop) {
            // 🔻 Scroll hacia abajo
            if (header) header.style.top = "-70px";
        } else {
            // 🔺 Scroll hacia arriba
            if (header) header.style.top = "0";
        }

        checkFooterVisibility();

        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    });

    // ⚡ Revisar también cuando la página termina de cargar
    window.addEventListener('load', checkFooterVisibility);
})();
