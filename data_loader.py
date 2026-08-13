# ==========================================
# ETF Rebalance AI
# Market Data Loader V4
#
# SPMO + PLUS 고배당주
#
# SPMO       -> yfinance
# PLUS 고배당주 -> pykrx
#
# 최근 1년
# N 거래일 변동률
# 변동률 차이
# 절대값
# Viewer 호환 price_data
# ==========================================

import yfinance as yf
import pandas as pd

from pykrx import stock

from datetime import datetime, timedelta


# ==========================================
# ETF 설정
# ==========================================

SPMO_TICKER = "SPMO"

# PLUS 고배당주
# 한국거래소 종목코드
PULS_TICKER = "161510"


# ==========================================
# 가격 데이터
# ==========================================

def get_price_data(
    analysis_years=1,
    comparison_days=30
):

    print(
        "시장 데이터를 가져오는 중..."
    )

    # --------------------------------------
    # 데이터 조회 기간
    #
    # 최근 1년 분석을 하더라도
    # N 거래일 전 가격이 필요하므로
    # 비교기간만큼 과거 데이터를 추가 확보
    # --------------------------------------

    today = datetime.now()

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

    end_date = (
        today
        +
        timedelta(days=1)
    )

    # 날짜 문자열
    start_str = start_date.strftime(
        "%Y%m%d"
    )

    end_str = today.strftime(
        "%Y%m%d"
    )

    # --------------------------------------
    # SPMO
    #
    # yfinance 사용
    # --------------------------------------

    spmo = yf.download(

        SPMO_TICKER,

        start=start_date,

        end=end_date,

        auto_adjust=True,

        progress=False
    )

    if spmo.empty:

        raise Exception(
            "SPMO 데이터를 가져오지 못했습니다."
        )

    spmo_close = spmo["Close"]

    # --------------------------------------
    # yfinance MultiIndex 대응
    # --------------------------------------

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

    # --------------------------------------
    # PLUS 고배당주
    #
    # pykrx 사용
    #
    # 종목코드 161510
    # --------------------------------------

    puls = stock.get_market_ohlcv_by_date(

        start_str,

        end_str,

        PULS_TICKER
    )

    if puls is None or puls.empty:

        raise Exception(
            "PLUS 고배당주(161510) 데이터를 "
            "가져오지 못했습니다."
        )

    # --------------------------------------
    # pykrx 날짜 정리
    # --------------------------------------

    puls.index = pd.to_datetime(
        puls.index
    )

    # --------------------------------------
    # pykrx 종가
    #
    # pykrx 컬럼:
    # 시가 / 고가 / 저가 / 종가 / 거래량 ...
    # --------------------------------------

    if "종가" not in puls.columns:

        raise Exception(
            "PLUS 고배당주 데이터에 "
            "'종가' 컬럼이 없습니다."
        )

    puls_close = pd.to_numeric(

        puls["종가"],

        errors="coerce"
    )

    # Viewer와 기존 코드 호환을 위해
    # 내부 이름은 PULS 유지

    puls_close.name = "PULS"

    # --------------------------------------
    # 두 ETF 가격 데이터 결합
    #
    # INNER JOIN을 사용해서
    # 두 ETF가 모두 거래된 날짜만 사용
    #
    # 중요:
    # SPMO는 미국 거래일
    # PLUS 고배당주는 한국 거래일
    #
    # 따라서 단순 날짜 병합이 아니라
    # 공통 거래일 기준으로 정렬
    # --------------------------------------

    data = pd.concat(

        [
            spmo_close,
            puls_close
        ],

        axis=1,

        join="inner"
    )

    # --------------------------------------
    # 숫자 변환
    # --------------------------------------

    data["SPMO"] = pd.to_numeric(

        data["SPMO"],

        errors="coerce"
    )

    data["PULS"] = pd.to_numeric(

        data["PULS"],

        errors="coerce"
    )

    # --------------------------------------
    # 결측치 제거
    # --------------------------------------

    data = data.dropna(

        subset=[
            "SPMO",
            "PULS"
        ]
    )

    # --------------------------------------
    # 날짜 정렬
    # --------------------------------------

    data.index = pd.to_datetime(
        data.index
    )

    data = data.sort_index()

    # --------------------------------------
    # 데이터 검증
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
        f"공통 거래일 데이터: {len(data)}일"
    )

    print(
        f"데이터 기간: "
        f"{data.index.min().strftime('%Y-%m-%d')}"
        f" ~ "
        f"{data.index.max().strftime('%Y-%m-%d')}"
    )

    return data


# ==========================================
# 최근 1년 분석 데이터
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
    #
    # 예:
    # comparison_days = 30
    #
    # 현재 가격 / 30 거래일 전 가격 - 1
    #
    # 즉 실제 거래일 기준 30일
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
    # 변동률 차이의 절대값
    #
    # AI 판단에서
    # 두 ETF 움직임의 차이 크기를 사용
    # --------------------------------------

    absolute_difference = (

        return_difference

    ).abs()

    # --------------------------------------
    # 분석 데이터 생성
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
    # 최근 N년만 사용
    # --------------------------------------

    latest_date = (
        data.index.max()
    )

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
    # 변동률 계산이 불가능한 초기 행 제거
    # --------------------------------------

    analysis = analysis.dropna()

    # --------------------------------------
    # 데이터 검증
    # --------------------------------------

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
    # 최근 N년 분석 데이터
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
    # Viewer 기존 반환 구조 유지
    # --------------------------------------

    return {

        "prices":
            prices,

        "price_data":
            data,

        "analysis_data":
            analysis_data

    }