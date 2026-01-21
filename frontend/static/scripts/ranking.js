document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("rankingChart").getContext("2d");

    let labels = carreras;
    let datasets = [];
    let lastPoints = [];
    let userColors = {}; // Almacenar los colores asignados a cada usuario

    // Generar colores aleatorios para cada usuario
    function getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Ordenar jugadores por su última puntuación
    let sortedPlayers = Object.keys(datosPuntos)
        .map(usuario => ({
            usuario: usuario,
            lastScore: datosPuntos[usuario][datosPuntos[usuario].length - 1]
        }))
        .sort((a, b) => b.lastScore - a.lastScore);

    // Asignar colores de las estrellas a los tres primeros
    let rankColors = ["#FFD700", "#C0C0C0", "#CD7F32"]; // Oro, Plata, Bronce
    let otherColors = {}; // Para el resto de los usuarios

    sortedPlayers.forEach((player, index) => {
        if (index < 3) {
            userColors[player.usuario] = rankColors[index]; // Colores oro, plata, bronce
        } else {
            userColors[player.usuario] = getRandomColor(); // Color aleatorio para el resto
        }
    });

    // Crear los datasets con los colores correctos
    sortedPlayers.forEach(player => {
        let usuario = player.usuario;
        let userData = datosPuntos[usuario];

        datasets.push({
            label: usuario,
            data: userData,
            borderColor: userColors[usuario], // Asignar el color correcto
            fill: false,
            tension: 0.3,
            pointBackgroundColor: "#FFFFFF",
            pointBorderColor: "#000000",
            borderWidth: 2,
        });

        // Solo asignar estrellas a los 3 primeros
        let playerRank = sortedPlayers.findIndex(p => p.usuario === usuario);
        if (playerRank < 3) {
            lastPoints.push({
                usuario: usuario,
                xIndex: userData.length - 1, // Índice del último punto
                y: userData[userData.length - 1], // Última puntuación
                icon: getStarIcon(playerRank) // Estrella según ranking
            });
        }
    });

    const chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        boxWidth: 10,
                        font: {
                            size: 10
                        }
                    }
                },
                title: {
                    display: true,
                    text: "Evolución de Puntos por Carrera",
                    font: {
                        size: 14
                    }
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Carreras",
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        maxRotation: 30,
                        minRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 5,
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: "Puntos Acumulados",
                        font: {
                            size: 12
                        }
                    },
                    beginAtZero: true,
                },
            },
            animation: {
                onComplete: () => {
                    drawStarIcons(chart);
                }
            }
        },
    });

    function drawStarIcons(chart) {
        const ctx = chart.ctx;
        ctx.font = "20px Arial";

        lastPoints.forEach(point => {
            const datasetIndex = datasets.findIndex(d => d.label === point.usuario);
            if (datasetIndex === -1) return;

            const meta = chart.getDatasetMeta(datasetIndex);
            const x = chart.scales.x.getPixelForValue(point.xIndex);
            const y = chart.scales.y.getPixelForValue(point.y);

            ctx.drawImage(point.icon, x - 10, y - 10, 20, 20);
        });
    }

    function getStarIcon(rank) {
        const icons = [
            new Image(),
            new Image(),
            new Image()
        ];
        icons[0].src = "/static/images/ranking/gold_star.png";  // 🥇 Oro
        icons[1].src = "/static/images/ranking/silver_star.png"; // 🥈 Plata
        icons[2].src = "/static/images/ranking/bronze_star.png"; // 🥉 Bronce

        return icons[rank] || null;
    }
});
