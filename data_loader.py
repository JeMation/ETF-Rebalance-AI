# ==========================================
# ETF Rebalance AI
# Market Data Loader V5
#
# SPMO + PLUS 고배당주
#
# SPMO       -> yfinance
# PLUS 고배당주 -> pykrx
#
# SQLite 증분 저장
# ==========================================

import yfinance as yf
import pandas as pd

from pykrx import stock

from datetime import datetime, timedelta
import sqlite3
import os


# ==========================================
# ETF 설정
# ==========================================

SPMO_TICKER = "SPMO"

# PLUS 고배당주
PULS_TICKER = "161510"


# ==========================================
# SQLite 설정
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "market_data.db"
)


# ==========================================
# SQLite 초기화
# ==========================================

def init_database():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_prices (
            date TEXT PRIMARY KEY,
            SPMO REAL,
            PULS REAL
        )
    """)

    conn.commit()

    conn.close()


# ==========================================
# SQLite 저장 데이터 불러오기
# ==========================================

def load_cached_data():

    init_database()

    conn = sqlite3.connect(DB_PATH)

    data = pd.read_sql_query(
        """
        SELECT date, SPMO, PULS
        FROM market_prices
        ORDER BY date
        """,
        conn
    )

    conn.close()

    if data.empty:
        return pd.DataFrame(
            columns=["SPMO", "PULS"]
        )

    data["date"] = pd.to_datetime(
        data["date"]
    )

    data = data.set_index("date")

    data["SPMO"] = pd.to_numeric(
        data["SPMO"],
        errors="coerce"
    )

    data["PULS"] = pd.to_numeric(
        data["PULS"],
        errors="coerce"
    )

    return data


# ==========================================
# SQLite 저장
# ==========================================

def save_data(data):

    if data is None or data.empty:
        return

    init_database()

    conn = sqlite3.connect(DB_PATH)

    save_data = data.copy()

    save_data.index = pd.to_datetime(
        save_data.index
    )

    # 날짜를 명시적으로 컬럼으로 생성
    save_data.index.name = "date"

    save_data = save_data.reset_index()

    save_data["date"] = (
        pd.to_datetime(
            save_data["date"]
        )
        .dt.strftime("%Y-%m-%d")
    )

    save_data.to_sql(
        "market_prices",
        conn,
        if_exists="append",
        index=False
    )

    conn.close()


# ==========================================
# SPMO 신규 데이터
# ==========================================

def get_spmo_new_data(
    start_date,
    end_date
):

    print(
        f"SPMO 신규 데이터 요청: "
        f"{start_date.strftime('%Y-%m-%d')} ~ "
        f"{end_date.strftime('%Y-%m-%d')}"
    )

    spmo = yf.download(

        SPMO_TICKER,

        start=start_date,

        end=end_date,

        auto_adjust=True,

        progress=False
    )

    if spmo.empty:
        return pd.Series(
            dtype=float,
            name="SPMO"
        )

    spmo_close = spmo["Close"]

    # yfinance MultiIndex 대응
    if isinstance(
        spmo_close,
        pd.DataFrame
    ):

        spmo_close = (
            spmo_close.iloc[:, 0]
        )

    spmo_close = pd.to_numeric(
        spmo_close,
        errors="coerce"
    )

    spmo_close.index = pd.to_datetime(
        spmo_close.index
    )

    spmo_close.name = "SPMO"

    return spmo_close.dropna()


# ==========================================
# PULS 신규 데이터
# ==========================================

def get_puls_new_data(
    start_date,
    end_date
):

    print(
        f"PULS 신규 데이터 요청: "
        f"{start_date.strftime('%Y-%m-%d')} ~ "
        f"{end_date.strftime('%Y-%m-%d')}"
    )

    start_str = start_date.strftime(
        "%Y%m%d"
    )

    end_str = end_date.strftime(
        "%Y%m%d"
    )

    puls = stock.get_market_ohlcv_by_date(

        start_str,

        end_str,

        PULS_TICKER
    )

    if puls is None or puls.empty:

        return pd.Series(
            dtype=float,
            name="PULS"
        )

    puls.index = pd.to_datetime(
        puls.index
    )

    if "종가" not in puls.columns:

        raise Exception(
            "PLUS 고배당주 데이터에 "
            "'종가' 컬럼이 없습니다."
        )

    puls_close = pd.to_numeric(

        puls["종가"],

        errors="coerce"
    )

    puls_close.name = "PULS"

    return puls_close.dropna()


# ==========================================
# 신규 데이터 수집
# ==========================================

def update_database(
    analysis_years=1,
    comparison_days=30
):

    cached = load_cached_data()

    today = datetime.now()

    # --------------------------------------
    # 최초 실행
    # --------------------------------------

    if cached.empty:

        print(
            "SQLite에 기존 데이터가 없습니다."
        )

        start_date = (

            today
            -
            timedelta(
                days=(
                    analysis_years * 365
                    +
                    comparison_days
                    +
                    30
                )
            )

        )

    else:

        # ----------------------------------
        # 마지막 저장 날짜 확인
        # ----------------------------------

        last_date = cached.index.max()

        start_date = (
            last_date.to_pydatetime()
            +
            timedelta(days=1)
        )

        print(
            f"SQLite 마지막 데이터: "
            f"{last_date.strftime('%Y-%m-%d')}"
        )

    # --------------------------------------
    # 이미 최신 데이터인 경우
    # --------------------------------------

    if start_date.date() > today.date():

        print(
            "새로운 데이터가 없습니다."
        )

        return cached

    # --------------------------------------
    # 신규 데이터 요청
    # --------------------------------------

    spmo_new = get_spmo_new_data(
        start_date,
        today + timedelta(days=1)
    )

    puls_new = get_puls_new_data(
        start_date,
        today
    )

    # --------------------------------------
    # 신규 데이터 결합
    # --------------------------------------

    new_data = pd.concat(
        [
            spmo_new,
            puls_new
        ],
        axis=1
    )

    new_data.index = pd.to_datetime(
        new_data.index
    )

    # --------------------------------------
    # 기존 데이터와 결합
    # --------------------------------------

    if not new_data.empty:

        new_data = new_data[
            ["SPMO", "PULS"]
        ]

        # ----------------------------------
        # 기존 데이터에 없는 날짜만 저장
        # ----------------------------------

        if not cached.empty:

            new_data = new_data[
                ~new_data.index.isin(
                    cached.index
                )
            ]

        if not new_data.empty:

            save_data(new_data)

            print(
                f"SQLite 신규 저장: "
                f"{len(new_data)}일"
            )

    # --------------------------------------
    # 최신 데이터 다시 읽기
    # --------------------------------------

    return load_cached_data()


# ==========================================
# 가격 데이터
# ==========================================

def get_price_data(
    analysis_years=1,
    comparison_days=30
):

    print(
        "시장 데이터를 확인하는 중..."
    )

    # --------------------------------------
    # SQLite 업데이트
    # --------------------------------------

    data = update_database(

        analysis_years=
            analysis_years,

        comparison_days=
            comparison_days
    )

    # --------------------------------------
    # 두 ETF 모두 존재하는 날짜만 사용
    # --------------------------------------

    data = data.dropna(
        subset=[
            "SPMO",
            "PULS"
        ]
    )

    data.index = pd.to_datetime(
        data.index
    )

    data = data.sort_index()

    # --------------------------------------
    # 분석에 필요한 데이터 확인
    # --------------------------------------

    if data.empty:

        raise Exception(
            "SPMO와 PLUS 고배당주의 "
            "공통 거래일 가격 데이터가 없습니다."
        )

    if len(data) <= comparison_days:

        raise Exception(

            "변동률 계산에 필요한 "
            "거래일 데이터가 부족합니다."
        )

    print(
        f"공통 거래일 데이터: "
        f"{len(data)}일"
    )

    print(
        f"데이터 기간: "
        f"{data.index.min().strftime('%Y-%m-%d')}"
        f" ~ "
        f"{data.index.max().strftime('%Y-%m-%d')}"
    )

    return data


# ==========================================
# 최근 N년 분석 데이터
# ==========================================

def build_analysis_data(
    data,
    analysis_years=1,
    comparison_days=30
):

    data = data.copy()

    data.index = pd.to_datetime(
        data.index
    )

    data = data.sort_index()

    # --------------------------------------
    # N 거래일 전 가격 기준
    # --------------------------------------

    spmo_return = (

        data["SPMO"]

        /

        data["SPMO"].shift(
            comparison_days
        )

        -

        1

    ) * 100

    puls_return = (

        data["PULS"]

        /

        data["PULS"].shift(
            comparison_days
        )

        -

        1

    ) * 100

    # --------------------------------------
    # 변동률 차이
    # --------------------------------------

    return_difference = (

        spmo_return

        -

        puls_return

    )

    # --------------------------------------
    # 절대값
    # --------------------------------------

    absolute_difference = (

        return_difference
    ).abs()

    # --------------------------------------
    # 분석 데이터
    # --------------------------------------

    analysis = pd.DataFrame({

        "SPMO_RETURN":
            spmo_return,

        "PULS_RETURN":
            puls_return,

        "return_difference":
            return_difference,

        "absolute_difference":
            absolute_difference

    })

    # --------------------------------------
    # 최근 N년
    # --------------------------------------

    latest_date = data.index.max()

    start_date = (

        latest_date

        -

        pd.DateOffset(
            years=analysis_years
        )

    )

    analysis = analysis[
        analysis.index >= start_date
    ]

    # --------------------------------------
    # 초기 NaN 제거
    # --------------------------------------

    analysis = analysis.dropna()

    if analysis.empty:

        raise Exception(
            "분석 가능한 데이터가 부족합니다."
        )

    return analysis


# ==========================================
# 현재 가격
# ==========================================

def get_current_prices(
    data
):

    if data is None or data.empty:

        raise Exception(
            "현재 가격을 확인할 데이터가 없습니다."
        )

    latest = data.iloc[-1]

    return {

        "SPMO":
            float(
                latest["SPMO"]
            ),

        "PULS":
            float(
                latest["PULS"]
            )

    }


# ==========================================
# 전체 AI 분석 데이터
# ==========================================

def get_market_analysis(

    analysis_years=1,

    comparison_days=30

):

    # --------------------------------------
    # 가격 데이터
    # --------------------------------------

    data = get_price_data(

        analysis_years=
            analysis_years,

        comparison_days=
            comparison_days

    )

    # --------------------------------------
    # 최근 N년 분석
    # --------------------------------------

    analysis_data = build_analysis_data(

        data,

        analysis_years=
            analysis_years,

        comparison_days=
            comparison_days

    )

    # --------------------------------------
    # 현재 가격
    # --------------------------------------

    prices = get_current_prices(
        data
    )

    # --------------------------------------
    # 기존 반환 구조 유지
    # --------------------------------------

    return {

        "prices":
            prices,

        "price_data":
            data,

        "analysis_data":
            analysis_data

    }