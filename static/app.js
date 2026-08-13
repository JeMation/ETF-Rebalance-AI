// ================================
// ETF Rebalance AI
// Multi ETF Comparison Chart
// ================================

document.addEventListener("DOMContentLoaded", () => {

    const ctx = document.getElementById("portfolioChart");
    const tickerSelect = document.getElementById("tickerSelect");

    let chart = null;

    async function loadChart() {

        // 선택된 ETF 목록
        const selectedTickers = Array.from(tickerSelect.selectedOptions)
            .map(option => option.value);

        if (selectedTickers.length === 0) {
            return;
        }

        // API 호출
        const params = selectedTickers
            .map(ticker => `tickers=${encodeURIComponent(ticker)}`)
            .join("&");

        const response = await fetch(`/api/compare?${params}`);
        const result = await response.json();

        // 첫 번째 ETF의 날짜 사용
        const labels = result[selectedTickers[0]].labels;

        // 여러 ETF Dataset 생성
        const datasets = selectedTickers.map(ticker => {

            return {

                label: ticker,

                data: result[ticker].normalized,

                borderWidth: 2,

                tension: 0.35,

                fill: false

            };

        });

        // 기존 차트 삭제
        if (chart) {
            chart.destroy();
        }

        chart = new Chart(ctx, {

            type: "line",

            data: {

                labels: labels,

                datasets: datasets

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                interaction: {
                    mode: "index",
                    intersect: false
                },

                plugins: {

                    legend: {
                        position: "top"
                    }

                },

                scales: {

                    y: {

                        beginAtZero: false,

                        title: {

                            display: true,

                            text: "Performance (%)"

                        }

                    }

                }

            }

        });

    }

    // 첫 실행
    loadChart();

    // ETF 선택 변경
    tickerSelect.addEventListener("change", loadChart);

    const rebalanceBtn = document.getElementById("rebalanceBtn");

if (rebalanceBtn) {

    rebalanceBtn.addEventListener("click", async () => {

        const totalAmount =
        Number(document.getElementById("totalAmount").value);

        const body = {

            total_amount: totalAmount,

            current: {
                QQQ: Number(document.getElementById("currentQQQ").value),
                SPY: Number(document.getElementById("currentSPY").value),
                SCHD: Number(document.getElementById("currentSCHD").value)
            },

            target: {
                QQQ: Number(document.getElementById("targetQQQ").value),
                SPY: Number(document.getElementById("targetSPY").value),
                SCHD: Number(document.getElementById("targetSCHD").value)
            }

        };

        const response = await fetch("/api/rebalance", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(body)

        });

        const result = await response.json();

        const table = document.getElementById("rebalanceTable");

        table.innerHTML = "";


        for (const ticker in result.result) {

            const data = result.result[ticker];


            let actionClass = "";

            if (data.action === "BUY") {

                actionClass = "text-success fw-bold";

            } 
            else if (data.action === "SELL") {

                actionClass = "text-danger fw-bold";

            }
            else {

                actionClass = "text-secondary fw-bold";

            }


            const row = `

            <tr>

                <td>${ticker}</td>

                <td>${data.current}%</td>

                <td>${data.target}%</td>

                <td>${data.difference}%</td>

                <td>
                    ${data.amount.toLocaleString()}원
                </td>

                <td class="${actionClass}">
                    ${data.action}
                </td>

            </tr>

            `;


            table.innerHTML += row;

        }

    });

}

});