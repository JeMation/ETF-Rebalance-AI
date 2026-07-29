// ================================
// ETF Rebalance AI
// Portfolio Performance Chart
// ================================

document.addEventListener("DOMContentLoaded", async () => {

    const ctx = document.getElementById("portfolioChart");

    if (!ctx) {
        console.error("portfolioChart를 찾을 수 없습니다.");
        return;
    }

    try {

        // FastAPI에서 데이터 가져오기
        const response = await fetch("/api/chart");
        const chartData = await response.json();

        new Chart(ctx, {

            type: "line",

            data: {

                labels: chartData.labels,

                datasets: [{

                    label: "QQQ Close Price",

                    data: chartData.values,

                    borderWidth: 3,
                    tension: 0.35,
                    fill: true

                }]
            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                scales: {

                    y: {
                        beginAtZero: false
                    }

                }

            }

        });

    } catch (error) {

        console.error("차트 데이터를 불러오지 못했습니다.", error);

    }

});