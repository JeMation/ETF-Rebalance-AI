# ==========================================
# ETF Rebalance AI
# Rebalance Decision Engine V4
#
# SPMO / PULS
# N 거래일 변동률 차이
#
# 최근 1년 극대점 분석
# 최소 극대점 기준
# 이상 극대점 분리
# 다음 극대점 크기 예측
# 리밸런싱 판단
# ==========================================

import numpy as np


class RebalanceAI:

    def __init__(
        self,
        metric_data,
        comparison_days=30,
        minimum_peak=10.0
    ):

        self.metric_data = metric_data.copy()

        self.comparison_days = int(
            comparison_days
        )

        self.minimum_peak = float(
            minimum_peak
        )

        # ----------------------------------
        # 데이터 검증
        # ----------------------------------

        if (
            "absolute_difference"
            not in self.metric_data.columns
        ):

            raise ValueError(
                "analysis_data에 "
                "'absolute_difference' 컬럼이 없습니다."
            )

        self.metric_data[
            "absolute_difference"
        ] = np.asarray(
            self.metric_data[
                "absolute_difference"
            ],
            dtype=float
        )

    # ======================================
    # 1. 극대점 탐색
    # ======================================

    def find_peaks(
        self,
        min_distance=10
    ):

        values = (
            self.metric_data[
                "absolute_difference"
            ]
            .astype(float)
            .tolist()
        )

        dates = (
            self.metric_data.index
            .tolist()
        )

        if len(values) < 3:

            return []

        peaks = []

        last_peak_index = -min_distance

        for i in range(
            1,
            len(values) - 1
        ):

            current = values[i]

            left = values[i - 1]

            right = values[i + 1]

            # ----------------------------------
            # 최소 극대점 기준
            #
            # Viewer에서 설정한
            # minimum_peak보다 작은 값은
            # 의미 있는 극대점으로 보지 않음
            # ----------------------------------

            if current < self.minimum_peak:

                continue

            # ----------------------------------
            # 기본 국소 극대점
            # ----------------------------------

            is_peak = (

                current >= left

                and

                current >= right

            )

            if not is_peak:

                continue

            # ----------------------------------
            # 너무 가까운 극대점 제거
            #
            # 가까운 극대점이 여러 개라면
            # 더 높은 값을 남김
            # ----------------------------------

            if (
                i - last_peak_index
                < min_distance
            ):

                if peaks:

                    previous = peaks[-1]

                    if (
                        current
                        >
                        previous["value"]
                    ):

                        peaks[-1] = {

                            "date":
                                dates[i].strftime(
                                    "%Y-%m-%d"
                                ),

                            "value":
                                round(
                                    current,
                                    4
                                ),

                            "index":
                                i

                        }

                        last_peak_index = i

                continue

            # ----------------------------------
            # 극대점 추가
            # ----------------------------------

            peaks.append({

                "date":
                    dates[i].strftime(
                        "%Y-%m-%d"
                    ),

                "value":
                    round(
                        current,
                        4
                    ),

                "index":
                    i

            })

            last_peak_index = i

        return peaks

    # ======================================
    # 2. 특이 극대점 제거
    # ======================================

    def remove_outliers(
        self,
        peaks
    ):

        if len(peaks) <= 2:

            return peaks, []

        values = np.array([

            float(
                peak["value"]
            )

            for peak in peaks

        ])

        median = float(
            np.median(values)
        )

        if median <= 0:

            return peaks, []

        # ----------------------------------
        # 특이 극대점 기준
        #
        # 정상 극대점 중앙값의
        # 1.5배 초과
        # ----------------------------------

        threshold = (
            median * 1.5
        )

        normal_peaks = []

        outlier_peaks = []

        for peak in peaks:

            value = float(
                peak["value"]
            )

            if value > threshold:

                outlier_peaks.append(
                    peak
                )

            else:

                normal_peaks.append(
                    peak
                )

        # ----------------------------------
        # 정상 데이터가 너무 적으면
        # 원본 유지
        #
        # 최소 2개의 극대점이 있어야
        # 추세 계산이 의미 있음
        # ----------------------------------

        if len(normal_peaks) < 2:

            return peaks, []

        return (
            normal_peaks,
            outlier_peaks
        )

    # ======================================
    # 3. 다음 극대점 예측
    # ======================================

    def predict_next_peak(
        self,
        peaks
    ):

        if not peaks:

            return None

        values = np.array([

            float(
                peak["value"]
            )

            for peak in peaks

        ])

        # ----------------------------------
        # 극대점 1개
        #
        # 과거 정보가 부족하므로
        # 마지막 극대점을 사용
        # ----------------------------------

        if len(values) == 1:

            prediction = values[-1]

        # ----------------------------------
        # 극대점 2개 이상
        #
        # 극대점의 크기 추세를
        # 선형으로 계산
        # ----------------------------------

        else:

            x = np.arange(
                len(values),
                dtype=float
            )

            slope, intercept = (
                np.polyfit(
                    x,
                    values,
                    1
                )
            )

            next_x = float(
                len(values)
            )

            prediction = (
                intercept
                +
                slope * next_x
            )

            # ----------------------------------
            # 지나친 외삽 방지
            #
            # 최근 정상 극대점 범위를
            # 크게 벗어나지 않도록 제한
            # ----------------------------------

            recent_min = float(
                np.min(values)
            )

            recent_max = float(
                np.max(values)
            )

            lower_limit = max(
                self.minimum_peak,
                recent_min
                -
                max(
                    recent_min * 0.5,
                    1.0
                )
            )

            upper_limit = (
                recent_max
                +
                max(
                    recent_max * 0.5,
                    1.0
                )
            )

            prediction = max(
                lower_limit,
                min(
                    prediction,
                    upper_limit
                )
            )

        return round(

            max(
                self.minimum_peak,
                float(prediction)
            ),

            4

        )

    # ======================================
    # 4. 현재 상태
    # ======================================

    def get_current_value(
        self
    ):

        if self.metric_data.empty:

            raise ValueError(
                "분석 데이터가 없습니다."
            )

        return float(

            self.metric_data[
                "absolute_difference"
            ]
            .iloc[-1]

        )

    # ======================================
    # 5. 분석
    # ======================================

    def analyze(
        self
    ):

        # ----------------------------------
        # 극대점 탐색
        # ----------------------------------

        peaks = self.find_peaks()

        # ----------------------------------
        # 이상 극대점 제거
        # ----------------------------------

        normal_peaks, outlier_peaks = (

            self.remove_outliers(
                peaks
            )

        )

        # ----------------------------------
        # 다음 극대점 예측
        # ----------------------------------

        predicted_peak = (

            self.predict_next_peak(
                normal_peaks
            )

        )

        # ----------------------------------
        # 예측값이 없는 경우
        #
        # 최소 극대점을 목표값으로 사용
        # ----------------------------------

        if predicted_peak is None:

            predicted_peak = (
                self.minimum_peak
            )

        # ----------------------------------
        # 최종 목표 극대점
        #
        # 최소 극대점보다 낮아질 수 없음
        # ----------------------------------

        target_peak = max(

            float(
                predicted_peak
            ),

            self.minimum_peak

        )

        # ----------------------------------
        # 현재값
        # ----------------------------------

        current_value = (
            self.get_current_value()
        )

        # ----------------------------------
        # 리밸런싱 판단
        #
        # 현재 변동률 차이가
        # 목표 극대점 이상이면
        # 리밸런싱
        # ----------------------------------

        if (
            current_value
            >=
            target_peak
        ):

            action = "REBALANCE"

        else:

            action = "HOLD"

        # ----------------------------------
        # 목표값까지 남은 차이
        # ----------------------------------

        difference = (

            target_peak

            -

            current_value

        )

        # ----------------------------------
        # 결과
        # ----------------------------------

        return {

            "ACTION":
                action,

            "CURRENT_VALUE":
                round(
                    current_value,
                    4
                ),

            "PREDICTED_PEAK":
                round(
                    predicted_peak,
                    4
                ),

            "MINIMUM_PEAK":
                round(
                    self.minimum_peak,
                    4
                ),

            "TARGET_PEAK":
                round(
                    target_peak,
                    4
                ),

            "DISTANCE_TO_TARGET":
                round(
                    max(
                        0.0,
                        difference
                    ),
                    4
                ),

            "PEAKS":
                normal_peaks,

            "OUTLIERS":
                outlier_peaks,

            "PEAK_COUNT":
                len(
                    normal_peaks
                ),

            "OUTLIER_COUNT":
                len(
                    outlier_peaks
                )

        }