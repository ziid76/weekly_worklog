from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render

# 그룹 정의 (Django auth Group 이름). apps.py 의 post_migrate signal 에서 자동 생성된다.
#   driving_log_users    — 운전기사. 본인 운행일지 작성/조회.
#   driving_log_managers — 지원팀 관리자. 전체 운행일지 조회·CSV. + 운전자 화면도 접근.
DRIVING_LOG_USER_GROUP = 'driving_log_users'
DRIVING_LOG_MANAGER_GROUP = 'driving_log_managers'


def is_driving_log_user(user):
    """운행일지(본인 목록/작성/편집) 접근 권한.

    driving_log_users 또는 driving_log_managers 그룹 소속, 또는 슈퍼유저.
    매니저도 동일하게 접근 가능 — 매니저 본인이 운전기사를 겸할 수 있고,
    그렇지 않더라도 본인 목록은 비어있을 뿐 접근 자체는 허용한다 (요건 §1).
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(
        name__in=[DRIVING_LOG_USER_GROUP, DRIVING_LOG_MANAGER_GROUP],
    ).exists()


def is_driving_log_manager(user):
    """운행일지 관리(전체 조회/CSV/이력) 접근 권한.

    driving_log_managers 그룹 소속 또는 슈퍼유저.

    Note: `is_staff` 는 의도적으로 사용하지 않는다. 기존 ITMS 의 스태프 권한 보유자
    (IT 운영자 등) 가 운행일지 관리 화면에 자동으로 노출되지 않도록 격리한다.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=DRIVING_LOG_MANAGER_GROUP).exists()


def is_driving_log_only_user(user):
    """운행일지 전용 사용자 — 다른 ITMS 메뉴 접근 차단(미들웨어 리다이렉트) 대상.

    그룹이 `{driving_log_users, driving_log_managers}` 의 부분집합일 때만 격리.
    다른 그룹(예: 기존 IT 사용자) 을 함께 가진 사용자는 일반 ITMS 사용자로 통과.

    슈퍼유저/스태프는 절대 격리 대상이 아니다 — 기존 ITMS 도 사용하기 때문.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return False
    group_names = set(user.groups.values_list('name', flat=True))
    if not group_names:
        return False
    return group_names.issubset({DRIVING_LOG_USER_GROUP, DRIVING_LOG_MANAGER_GROUP})


class DrivingLogUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """운전자(driving_log_users 또는 driving_log_managers) 전용 뷰에 적용."""

    raise_exception = False

    def test_func(self):
        return is_driving_log_user(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return render(
            self.request,
            'driving_log/no_permission.html',
            status=403,
        )


class DrivingLogManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """지원팀 관리자(driving_log_managers) 전용 뷰에 적용.

    `is_staff` 가 아니라 `driving_log_managers` 그룹 멤버십으로 판정한다 —
    기존 IT 스태프가 의도치 않게 운행일지 관리 화면을 보지 않도록.
    """

    raise_exception = False

    def test_func(self):
        return is_driving_log_manager(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return render(
            self.request,
            'driving_log/no_permission.html',
            status=403,
        )
