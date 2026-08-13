# ==========================================
# ETF Rebalance AI
# Main Application V3.1
#
# SPMO / PULS 반비례 패턴 분석
# + 기초 데이터 Viewer
# + 극대점 그래프
# ==========================================

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from data_loader import get_market_analysis
from analysis.rebalance_engine import RebalanceAI


# ==========================================
# FastAPI
# ==========================================

app = FastAPI(

    title="ETF Rebalance AI",

    description=(
        "SPMO / PULS 반비례 패턴 기반 "
        "리밸런싱 분석 시스템"
    ),

    version="3.1.0"

)


# ==========================================
# Static
# ==========================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# ==========================================
# Portfolio
# ==========================================

INVESTMENT_AMOUNT = 10_000_000

PULS_VALUE = 4_400_000

SPMO_VALUE = 5_600_000


# ==========================================
# Portfolio 계산
# ==========================================

def get_portfolio():

    total = (
        PULS_VALUE
        +
        SPMO_VALUE
    )

    if total <= 0:

        raise ValueError(
            "포트폴리오 금액은 0보다 커야 합니다."
        )

    puls_ratio = (
        PULS_VALUE
        /
        total
    ) * 100

    spmo_ratio = (
        SPMO_VALUE
        /
        total
    ) * 100

    return {

        "total":
            total,

        "PULS":
            PULS_VALUE,

        "SPMO":
            SPMO_VALUE,

        "PULS_RATIO":
            round(
                puls_ratio,
                2
            ),

        "SPMO_RATIO":
            round(
                spmo_ratio,
                2
            )

    }


# ==========================================
# 날짜 포맷
# ==========================================

def format_date(value):

    try:

        return value.strftime(
            "%Y-%m-%d"
        )

    except Exception:

        return str(value)[:10]


# ==========================================
# HTML
# ==========================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def home():

    portfolio = get_portfolio()

    return f"""

<!DOCTYPE html>

<html lang="ko">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
ETF Rebalance AI
</title>

<link
    rel="stylesheet"
    href="/static/style.css"
>

<!-- Chart.js -->
<script
    src="https://cdn.jsdelivr.net/npm/chart.js"
></script>

<style>

.analysis-box {{

    margin-top: 20px;

    padding: 18px;

    border-radius: 10px;

    background: #f7f7f7;

}}

.setting-row {{

    display: flex;

    align-items: center;

    gap: 8px;

    margin-bottom: 12px;

}}

.setting-row label {{

    width: 120px;

}}

.setting-row input {{

    width: 90px;

    padding: 7px;

    font-size: 16px;

}}

.viewer-button {{

    margin-top: 15px;

    margin-right: 8px;

    padding: 10px 16px;

    cursor: pointer;

}}

#chart-container {{

    position: relative;

    width: 100%;

    height: 450px;

}}

.data-table-wrapper {{

    overflow-x: auto;

    margin-top: 15px;

}}

.data-table {{

    width: 100%;

    border-collapse: collapse;

    min-width: 850px;

}}

.data-table th,

.data-table td {{

    border: 1px solid #ddd;

    padding: 7px 9px;

    text-align: right;

    white-space: nowrap;

}}

.data-table th:first-child,

.data-table td:first-child {{

    text-align: center;

}}

.data-table th {{

    background: #eeeeee;

}}

.peak-row {{

    font-weight: bold;

}}

.peak-mark {{

    font-weight: bold;

}}

.status-rebalance {{

    font-size: 28px;

    font-weight: bold;

}}

.status-hold {{

    font-size: 28px;

    font-weight: bold;

}}

</style>

</head>


<body>

<div class="container">


<h1>
ETF Rebalance AI
</h1>


<p>
SPMO / PULS 반비례 패턴 기반
리밸런싱 분석 시스템
</p>


<!-- ================================= -->
<!-- Portfolio -->
<!-- ================================= -->

<div class="card">

<h2>
현재 포트폴리오
</h2>


<p>

총 투자금

<strong>
{portfolio["total"]:,}원
</strong>

</p>


<hr>


<p>

PULS

<strong>
{portfolio["PULS"]:,}원
({portfolio["PULS_RATIO"]}%)
</strong>

</p>


<p>

SPMO

<strong>
{portfolio["SPMO"]:,}원
({portfolio["SPMO_RATIO"]}%)
</strong>

</p>

</div>


<!-- ================================= -->
<!-- AI 설정 -->
<!-- ================================= -->

<div class="card">

<h2>
AI 분석 설정
</h2>


<div class="setting-row">

<label for="analysisYears">
분석 기간
</label>

<input
    id="analysisYears"
    type="number"
    min="1"
    max="10"
    step="1"
    value="1"
>

<span>
년
</span>

</div>


<div class="setting-row">

<label for="comparisonDays">
ETF 비교 기간
</label>

<input
    id="comparisonDays"
    type="number"
    min="1"
    max="250"
    step="1"
    value="30"
>

<span>
거래일
</span>

</div>


<div class="setting-row">

<label for="minimumPeak">
최저 극대점
</label>

<input
    id="minimumPeak"
    type="number"
    min="0"
    max="100"
    step="0.1"
    value="10"
>

<span>
%
</span>

</div>


<button
    class="viewer-button"
    onclick="runAnalysis()"
>
AI 분석 시작
</button>


<div
    id="loading"
    style="display:none;"
>

<p>
시장 데이터를 분석하고 있습니다...
</p>

</div>

</div>


<!-- ================================= -->
<!-- AI 결과 -->
<!-- ================================= -->

<div
    class="card"
    id="result"
>

<p>
분석 설정 후
AI 분석 시작 버튼을 눌러주세요.
</p>

</div>


<!-- ================================= -->
<!-- 그래프 -->
<!-- ================================= -->

<div
    class="card"
    id="graphCard"
    style="display:none;"
>

<h2>
절대값 극대점 그래프
</h2>


<p>
SPMO와 PULS의 설정된 거래일 변동률 차이의 절대값입니다.
</p>


<div id="chart-container">

<canvas id="peakChart"></canvas>

</div>

</div>


<!-- ================================= -->
<!-- 기초 데이터 -->
<!-- ================================= -->

<div
    class="card"
    id="dataCard"
    style="display:none;"
>

<h2>
기초 데이터
</h2>


<p>
AI가 실제 계산에 사용한 최근 데이터를 확인할 수 있습니다.
</p>


<p id="dataInfo"></p>


<div class="data-table-wrapper">

<table class="data-table">

<thead>

<tr>

<th>
날짜
</th>

<th>
SPMO 가격
</th>

<th>
PULS 가격
</th>

<th>
SPMO 변동률
</th>

<th>
PULS 변동률
</th>

<th>
절대값
</th>

<th>
극대점
</th>

</tr>

</thead>

<tbody
    id="dataTableBody"
>
</tbody>

</table>

</div>

</div>


<script>

let peakChart = null;


// ======================================
// 숫자 포맷
// ======================================

function number(value, digits = 2) {{

    const n = Number(value);

    if (!Number.isFinite(n)) {{

        return "-";

    }}

    return n.toFixed(digits);

}}


// ======================================
// AI 분석
// ======================================

async function runAnalysis() {{

    const result =
        document.getElementById(
            "result"
        );


    const loading =
        document.getElementById(
            "loading"
        );


    const analysisYears =
        Number(
            document.getElementById(
                "analysisYears"
            ).value
        );


    const comparisonDays =
        Number(
            document.getElementById(
                "comparisonDays"
            ).value
        );


    const minimumPeak =
        Number(
            document.getElementById(
                "minimumPeak"
            ).value
        );


    // ==================================
    // 입력값 검증
    // ==================================

    if (
        !Number.isFinite(
            analysisYears
        )
        ||
        analysisYears < 1
    ) {{

        alert(
            "분석 기간은 1년 이상이어야 합니다."
        );

        return;

    }}


    if (
        !Number.isFinite(
            comparisonDays
        )
        ||
        comparisonDays < 1
    ) {{

        alert(
            "비교 기간은 1일 이상이어야 합니다."
        );

        return;

    }}


    if (
        !Number.isFinite(
            minimumPeak
        )
        ||
        minimumPeak < 0
    ) {{

        alert(
            "최저 극대점은 0% 이상이어야 합니다."
        );

        return;

    }}


    result.innerHTML = "";

    loading.style.display = "block";


    try {{

        const url =
            "/api/analyze"
            +
            "?analysis_years="
            +
            encodeURIComponent(
                analysisYears
            )
            +
            "&comparison_days="
            +
            encodeURIComponent(
                comparisonDays
            )
            +
            "&minimum_peak="
            +
            encodeURIComponent(
                minimumPeak
            );


        const response =
            await fetch(url);


        if (!response.ok) {{

            const errorData =
                await response.json()
                    .catch(
                        () => null
                    );


            throw new Error(

                errorData
                &&
                errorData.detail

                    ?

                errorData.detail

                    :

                "서버 분석 오류"

            );

        }}


        const data =
            await response.json();


        renderResult(data);

        renderChart(data);

        renderTable(data);


        document.getElementById(
            "graphCard"
        ).style.display = "block";


        document.getElementById(
            "dataCard"
        ).style.display = "block";


    }}

    catch(error) {{

        result.innerHTML = `

            <hr>

            <h3>
                분석 오류
            </h3>

            <p>
                ${{error.message}}
            </p>

        `;

        document.getElementById(
            "graphCard"
        ).style.display = "none";


        document.getElementById(
            "dataCard"
        ).style.display = "none";

    }}

    finally {{

        loading.style.display = "none";

    }}

}}


// ======================================
// 결과 표시
// ======================================

function renderResult(data) {{

    const result =
        document.getElementById(
            "result"
        );


    const isRebalance =
        data.action
        ===
        "REBALANCE";


    const actionText =
        isRebalance
            ?
        "리밸런싱 추천"
            :
        "리밸런싱 대기";


    const actionClass =
        isRebalance
            ?
        "status-rebalance"
            :
        "status-hold";


    result.innerHTML = `

        <hr>


        <h2>
            AI 분석 결과
        </h2>


        <div class="analysis-box">

            <h3>
                현재 상태
            </h3>

            <p class="${{actionClass}}">

                ${{actionText}}

            </p>

        </div>


        <div class="analysis-box">

            <h3>
                분석 설정
            </h3>

            <p>
                분석 기간:
                <strong>
                    ${{data.analysis_years}}년
                </strong>
            </p>

            <p>
                ETF 비교 기간:
                <strong>
                    ${{data.comparison_days}}거래일
                </strong>
            </p>

            <p>
                최저 극대점:
                <strong>
                    ${{number(data.minimum_peak)}}%
                </strong>
            </p>

        </div>


        <div class="analysis-box">

            <h3>
                현재 절대값
            </h3>

            <p style="font-size:28px;">

                <strong>
                    ${{number(data.current_value)}}%
                </strong>

            </p>

            <p>
                SPMO
                <strong>
                    ${{number(data.current_returns.SPMO)}}%
                </strong>
            </p>

            <p>
                PULS
                <strong>
                    ${{number(data.current_returns.PULS)}}%
                </strong>
            </p>

            <p>
                절대값 =
                |SPMO 변동률 - PULS 변동률|
            </p>

        </div>


        <div class="analysis-box">

            <h3>
                다음 극대점 예측
            </h3>

            <p>
                AI 예상 다음 극대점:
                <strong>
                    ${{number(data.predicted_peak)}}%
                </strong>
            </p>

            <p>
                최저 극대점 설정:
                <strong>
                    ${{number(data.minimum_peak)}}%
                </strong>
            </p>

            <p style="font-size:22px;">

                최종 리밸런싱 기준:
                <strong>
                    ${{number(data.target_peak)}}%
                </strong>

            </p>

        </div>


        <div class="analysis-box">

            <h3>
                리밸런싱 기준까지
            </h3>

            <p>

                현재:

                <strong>
                    ${{number(data.current_value)}}%
                </strong>

            </p>


            <p>

                목표:

                <strong>
                    ${{number(data.target_peak)}}%
                </strong>

            </p>


            <p>

                남은 차이:

                <strong>
                    ${{number(data.distance_to_target)}}%
                </strong>

            </p>

        </div>


        <div class="analysis-box">

            <h3>
                극대점 분석
            </h3>

            <p>
                정상 극대점:
                <strong>
                    ${{data.peak_count}}개
                </strong>
            </p>

            <p>
                특이 극대점:
                <strong>
                    ${{data.outlier_count}}개
                </strong>
            </p>

        </div>

    `;

}}


// ======================================
// 그래프
// ======================================

function renderChart(data) {{

    const canvas =
        document.getElementById(
            "peakChart"
        );


    if (peakChart !== null) {{

        peakChart.destroy();

        peakChart = null;

    }}


    const rows =
        data.chart_data;


    const labels =
        rows.map(
            row => row.date
        );


    const values =
        rows.map(
            row => row.absolute_difference
        );


    const peakValues =
        rows.map(
            row =>

                row.is_peak
                    ?
                row.absolute_difference
                    :
                null

        );


    const targetValues =
        rows.map(
            () =>
                data.target_peak
        );


    const minimumValues =
        rows.map(
            () =>
                data.minimum_peak
        );


    peakChart =
        new Chart(

            canvas,

            {{

                type: "line",


                data: {{

                    labels: labels,


                    datasets: [

                        {{

                            label:
                                "절대값",

                            data:
                                values,

                            borderWidth:
                                2,

                            pointRadius:
                                0,

                            tension:
                                0.1

                        }},


                        {{

                            label:
                                "실제 극대점",

                            data:
                                peakValues,

                            borderWidth:
                                0,

                            pointRadius:
                                5,

                            pointHoverRadius:
                                7,

                            showLine:
                                false

                        }},


                        {{

                            label:
                                "다음 극대점 기준",

                            data:
                                targetValues,

                            borderWidth:
                                2,

                            borderDash:
                                [8, 5],

                            pointRadius:
                                0

                        }},


                        {{

                            label:
                                "최저 극대점",

                            data:
                                minimumValues,

                            borderWidth:
                                1,

                            borderDash:
                                [4, 4],

                            pointRadius:
                                0

                        }}

                    ]

                }},


                options: {{

                    responsive:
                        true,

                    maintainAspectRatio:
                        false,


                    interaction: {{

                        mode:
                            "index",

                        intersect:
                            false

                    }},


                    scales: {{

                        y: {{

                            title: {{

                                display:
                                    true,

                                text:
                                    "절대값 (%)"

                            }},


                            ticks: {{

                                callback:
                                    function(value) {{

                                        return value
                                            + "%";

                                    }}

                            }}

                        }},


                        x: {{

                            ticks: {{

                                maxTicksLimit:
                                    12

                            }}

                        }}

                    }},


                    plugins: {{

                        tooltip: {{

                            callbacks: {{

                                label:
                                    function(context) {{

                                        return (
                                            context.dataset.label
                                            +
                                            ": "
                                            +
                                            number(
                                                context.raw
                                            )
                                            +
                                            "%"
                                        );

                                    }}

                            }}

                        }}

                    }}

                }}

            }}

        );

}}


// ======================================
// 기초 데이터 표
// ======================================

function renderTable(data) {{

    const body =
        document.getElementById(
            "dataTableBody"
        );


    const info =
        document.getElementById(
            "dataInfo"
        );


    body.innerHTML = "";


    const rows =
        data.table_data;


    info.innerHTML =

        "전체 분석 데이터 "
        +
        "<strong>"
        +
        data.data_count
        +
        "</strong>"
        +
        "개 중 최근 "
        +
        "<strong>"
        +
        rows.length
        +
        "</strong>"
        +
        "개 표시";


    rows.forEach(
        row => {{

            const tr =
                document.createElement(
                    "tr"
                );


            if (row.is_peak) {{

                tr.classList.add(
                    "peak-row"
                );

            }}


            const peakText =
                row.is_peak
                    ?
                "★ 극대점"
                    :
                "";


            tr.innerHTML = `

                <td>
                    ${{row.date}}
                </td>

                <td>
                    ${{number(row.spmo_price)}}
                </td>

                <td>
                    ${{number(row.puls_price)}}
                </td>

                <td>
                    ${{number(row.spmo_return)}}%
                </td>

                <td>
                    ${{number(row.puls_return)}}%
                </td>

                <td>
                    ${{number(row.absolute_difference)}}%
                </td>

                <td class="peak-mark">
                    ${{peakText}}
                </td>

            `;


            body.appendChild(
                tr
            );

        }}
    );

}}


</script>


</body>

</html>

"""


# ==========================================
# AI 분석 API
# ==========================================

@app.get("/api/analyze")
def analyze(

    analysis_years: int = Query(
        1,
        ge=1,
        le=10
    ),

    comparison_days: int = Query(
        30,
        ge=1,
        le=250
    ),

    minimum_peak: float = Query(
        10.0,
        ge=0,
        le=100
    )

):

    # ======================================
    # Portfolio
    # ======================================

    portfolio = get_portfolio()


    # ======================================
    # Market Data
    # ======================================

    market = get_market_analysis(

        analysis_years=
            analysis_years,

        comparison_days=
            comparison_days

    )


    analysis_data = (
        market["analysis_data"]
    )


    # ======================================
    # AI Engine
    # ======================================

    ai = RebalanceAI(

        metric_data=
            analysis_data,

        comparison_days=
            comparison_days,

        minimum_peak=
            minimum_peak

    )


    result = ai.analyze()


    # ======================================
    # 극대점 날짜 집합
    # ======================================

    peak_dates = {

        peak["date"]

        for peak in result["PEAKS"]

    }


    outlier_dates = {

        peak["date"]

        for peak in result["OUTLIERS"]

    }


    # ======================================
    # 전체 Chart Data
    # ======================================

    chart_data = []


    for index, row in analysis_data.iterrows():

        date = format_date(
            index
        )


        chart_data.append({

            "date":
                date,

            "absolute_difference":
                round(
                    float(
                        row[
                            "absolute_difference"
                        ]
                    ),
                    4
                ),

            "is_peak":
                date in peak_dates,

            "is_outlier":
                date in outlier_dates

        })


    # ======================================
    # Table Data
    #
    # 최근 50개만 Viewer 표시
    # ======================================

    recent_data = (
        analysis_data
        .tail(50)
        .iloc[::-1]
    )


    table_data = []


    for index, row in recent_data.iterrows():

        date = format_date(
            index
        )


        table_data.append({

            "date":
                date,

            "spmo_price":
                round(
                    float(
                        market[
                            "price_data"
                        ].loc[
                            index,
                            "SPMO"
                        ]
                    ),
                    4
                )
                if "price_data" in market
                else None,

            "puls_price":
                round(
                    float(
                        market[
                            "price_data"
                        ].loc[
                            index,
                            "PULS"
                        ]
                    ),
                    4
                )
                if "price_data" in market
                else None,

            "spmo_return":
                round(
                    float(
                        row[
                            "SPMO_RETURN"
                        ]
                    ),
                    4
                ),

            "puls_return":
                round(
                    float(
                        row[
                            "PULS_RETURN"
                        ]
                    ),
                    4
                ),

            "absolute_difference":
                round(
                    float(
                        row[
                            "absolute_difference"
                        ]
                    ),
                    4
                ),

            "is_peak":
                date in peak_dates,

            "is_outlier":
                date in outlier_dates

        })


    # ======================================
    # 현재 변동률
    # ======================================

    latest_metric = (
        analysis_data.iloc[-1]
    )


    current_spmo_return = float(

        latest_metric[
            "SPMO_RETURN"
        ]

    )


    current_puls_return = float(

        latest_metric[
            "PULS_RETURN"
        ]

    )


    # ======================================
    # 결과
    # ======================================

    return {

        "investment":
            portfolio["total"],

        "puls_value":
            portfolio["PULS"],

        "spmo_value":
            portfolio["SPMO"],

        "puls_ratio":
            portfolio["PULS_RATIO"],

        "spmo_ratio":
            portfolio["SPMO_RATIO"],


        "prices":
            market["prices"],


        "analysis_years":
            analysis_years,


        "comparison_days":
            comparison_days,


        "minimum_peak":
            float(
                minimum_peak
            ),


        "current_returns": {

            "SPMO":
                round(
                    current_spmo_return,
                    4
                ),

            "PULS":
                round(
                    current_puls_return,
                    4
                )

        },


        "current_value":
            result[
                "CURRENT_VALUE"
            ],


        "predicted_peak":
            result[
                "PREDICTED_PEAK"
            ],


        "target_peak":
            result[
                "TARGET_PEAK"
            ],


        "distance_to_target":
            result[
                "DISTANCE_TO_TARGET"
            ],


        "action":
            result[
                "ACTION"
            ],


        "peaks":
            result[
                "PEAKS"
            ],


        "outliers":
            result[
                "OUTLIERS"
            ],


        "peak_count":
            result[
                "PEAK_COUNT"
            ],


        "outlier_count":
            result[
                "OUTLIER_COUNT"
            ],


        "chart_data":
            chart_data,


        "table_data":
            table_data,


        "data_count":
            len(
                analysis_data
            )

    }