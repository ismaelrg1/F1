(() => {
    const raceCards = document.querySelectorAll(".race-card");

    let now = new Date();
    let nextRaceCard = null;
    let minTimeDiff = Infinity;

    raceCards.forEach(card => {
        const dateElement = card.querySelector(".date span");
        if (dateElement) {
            const dateText = dateElement.textContent.trim();
            const [day, monthStr] = dateText.split("-");
            const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const month = months.indexOf(monthStr);

            const raceDate = new Date(now.getFullYear(), month, parseInt(day));
            const timeDiff = raceDate - now;

            if (timeDiff > 0 && timeDiff < minTimeDiff) {
                minTimeDiff = timeDiff;
                nextRaceCard = card;
            }
        }
    });

    if (nextRaceCard) {
        nextRaceCard.classList.add("next-race");

        // Crear estilo si no existe
        if (!document.getElementById('next-race-style')) {
            const style = document.createElement('style');
            style.id = 'next-race-style';
            style.textContent = `
                .next-race {
                    border: 3px solid #ff0000;
                    box-shadow: 0 0 15px rgba(255, 0, 0, 0.7);
                    animation: pulse 2s infinite;
                    scroll-margin-top: 100px;
                }

                @keyframes pulse {
                    0% { transform: scale(1); box-shadow: 0 0 15px rgba(255, 0, 0, 0.7); }
                    50% { transform: scale(1.05); box-shadow: 0 0 25px rgba(255, 0, 0, 0.9); }
                    100% { transform: scale(1); box-shadow: 0 0 15px rgba(255, 0, 0, 0.7); }
                }
            `;
            document.head.appendChild(style);
        }

        // 🚀 Antes de hacer scroll automático, avisamos para ignorar scroll
        window.ignoreScroll = true;
        setTimeout(() => {
            nextRaceCard.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 300);

        // 🕓 Después de un tiempo (por ejemplo 1000ms), dejamos de ignorar scrolls
        setTimeout(() => {
            window.ignoreScroll = false;
        }, 1300); 
    }
})();
