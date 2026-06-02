"""초과근무 계산 헬퍼.

규칙:
- 평일(월~금) 휴일 아님: 09:00~18:00 정규근무 시간을 제외한 시간이 초과근무.
- 토/일 (자동 휴일) 또는 사용자 수동 휴일 체크: 운행 전체 시간이 초과근무.
- 자정을 넘는 운행(end_time <= start_time)은 본 설계서에서 0분 처리.
  (자정 넘김 정책은 추후 정책 결정 후 갱신)
"""
from datetime import datetime, time

WORK_START = time(9, 0)
WORK_END = time(18, 0)


def calc_overtime_minutes(log_date, start_time, end_time, is_holiday):
    """주어진 1일치 정보로 초과근무 분 수를 반환."""
    if log_date is None or start_time is None or end_time is None:
        return 0
    s = datetime.combine(log_date, start_time)
    e = datetime.combine(log_date, end_time)
    if e <= s:
        return 0
    total_min = int((e - s).total_seconds() // 60)

    weekday = log_date.weekday()  # 0=월 ... 5=토 6=일
    is_weekend = weekday >= 5
    if is_weekend or is_holiday:
        return total_min

    work_s = datetime.combine(log_date, WORK_START)
    work_e = datetime.combine(log_date, WORK_END)
    overlap_s = max(s, work_s)
    overlap_e = min(e, work_e)
    overlap_min = max(0, int((overlap_e - overlap_s).total_seconds() // 60))
    return total_min - overlap_min


def calc_run_minutes(log_date, start_time, end_time):
    """주어진 1일치 정보로 운행 시간(분) 을 반환.

    end_time - start_time 단순 차감. 자정 넘는 운행은 운영 정책상 일자 2건으로
    분리 입력하므로 end > start 가정. end <= start 면 0분.
    """
    if log_date is None or start_time is None or end_time is None:
        return 0
    s = datetime.combine(log_date, start_time)
    e = datetime.combine(log_date, end_time)
    if e <= s:
        return 0
    return int((e - s).total_seconds() // 60)


def format_minutes(minutes):
    """분 수를 'NN시간 MM분' 형태로 변환."""
    m = int(minutes or 0)
    return f'{m // 60}시간 {m % 60}분'
