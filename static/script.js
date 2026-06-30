document.querySelectorAll("[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        const message = form.dataset.confirm || "Are you sure?";
        if (!window.confirm(message)) {
            event.preventDefault();
        }
    });
});

const chartCanvas = document.querySelector("#progressChart");
const chartDataScript = document.querySelector("#chartData");

if (chartCanvas && chartDataScript && window.Chart) {
    const workouts = JSON.parse(chartDataScript.textContent || "[]");

    new Chart(chartCanvas, {
        type: "line",
        data: {
            labels: workouts.map((workout) => workout.label),
            datasets: [
                {
                    label: "Workout volume",
                    data: workouts.map((workout) => workout.volume),
                    borderColor: "#34d399",
                    backgroundColor: "rgba(52, 211, 153, 0.14)",
                    fill: true,
                    tension: 0.32,
                    pointBackgroundColor: "#f59e0b",
                    pointBorderColor: "#07111f",
                    pointRadius: 5,
                    pointHoverRadius: 7,
                },
            ],
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            scales: {
                x: {
                    grid: {
                        color: "rgba(255, 255, 255, 0.07)",
                    },
                    ticks: {
                        color: "#9aa8bd",
                    },
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: "rgba(255, 255, 255, 0.07)",
                    },
                    ticks: {
                        color: "#9aa8bd",
                    },
                    title: {
                        display: true,
                        text: "Sets x reps x weight",
                        color: "#dbe7f5",
                    },
                },
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: "rgba(7, 11, 20, 0.94)",
                    borderColor: "rgba(255, 255, 255, 0.14)",
                    borderWidth: 1,
                    titleColor: "#f6f8ff",
                    bodyColor: "#dbe7f5",
                    callbacks: {
                        label: (context) => `Volume: ${context.parsed.y}`,
                    },
                },
            },
        },
    });
}
