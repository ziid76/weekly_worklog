from .permissions import in_driving_log_manager_group, is_driving_log_only_user


def driving_only_flag(request):
    """basic.html 의 사이드바 분기용 컨텍스트 변수.

    템플릿 변수:
      - ``is_driving_only_user``  — 운행일지 전용 사용자 (드라이버 또는 매니저)
                                     로 다른 ITMS 메뉴 접근이 차단된 사람.
      - ``is_driving_log_manager`` — driving_log_managers 그룹 보유자만 True.
                                     사이드바의 [운행일지 관리]/[임원 관리] 메뉴 노출 가드.
                                     슈퍼유저/스태프는 그룹이 없으면 메뉴가 보이지 않는다
                                     (뷰 접근 권한과는 별개 — 접근은 슈퍼유저도 가능).
    """
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        return {
            'is_driving_only_user': False,
            'is_driving_log_manager': False,
        }
    return {
        'is_driving_only_user': is_driving_log_only_user(user),
        'is_driving_log_manager': in_driving_log_manager_group(user),
    }
