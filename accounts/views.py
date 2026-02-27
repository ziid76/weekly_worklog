from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .models import UserProfile
from .forms import UserProfileForm, UserUpdateForm, UserCreationFormWithProfile, TeamCreationForm, FirstLoginPasswordChangeForm
from teams.models import Team, TeamMembership
from common.message_views import send_kakao_message


class CustomLoginView(LoginView):
    """커스텀 로그인 뷰 - 첫 로그인 사용자 체크"""
    
    def get_success_url(self):
        # 로그인 성공 후 첫 로그인 여부 체크
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_first_login:
            return '/useraccounts/first-login-password-change/'
        return super().get_success_url()


def is_staff_or_superuser(user):
    """관리자 권한 확인"""
    return user.is_staff or user.is_superuser

@login_required
def first_login_password_change(request):
    """첫 로그인 시 패스워드 변경"""
    # 이미 패스워드를 변경한 사용자는 대시보드로 리다이렉트
    if not request.user.profile.is_first_login:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FirstLoginPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # 첫 로그인 상태 업데이트
            profile = user.profile
            profile.is_first_login = False
            profile.password_changed_at = timezone.now()
            profile.save()
            
            messages.success(request, '비밀번호가 성공적으로 변경되었습니다.')
            return redirect('login')
        else:
            messages.error(request, '비밀번호 변경에 실패했습니다. 입력 정보를 다시 확인해주세요.')
    else:
        form = FirstLoginPasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'user': request.user,
    }
    
    return render(request, 'accounts/first_login_password_change.html', context)

@login_required
def profile_edit(request):
    """사용자 프로필 편집"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user = request.user
        logger.info(f"Profile edit started for user: {user.username}")
        
        # UserProfile이 없으면 생성
        profile, created = UserProfile.objects.get_or_create(user=user)
        logger.info(f"Profile {'created' if created else 'found'} for user: {user.username}")
        
        if request.method == 'POST':
            logger.info("Processing POST request")
            logger.info(f"POST data: {request.POST}")
            
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            
            logger.info(f"User form valid: {user_form.is_valid()}")
            logger.info(f"Profile form valid: {profile_form.is_valid()}")
            
            if not user_form.is_valid():
                logger.error(f"User form errors: {user_form.errors}")
            if not profile_form.is_valid():
                logger.error(f"Profile form errors: {profile_form.errors}")
            
            if user_form.is_valid() and profile_form.is_valid():
                logger.info("Both forms valid, saving...")
                user_form.save()
                logger.info("User form saved")
                profile_form.save()
                logger.info("Profile form saved")
                messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
                return redirect('profile_edit')
            else:
                messages.error(request, '입력된 정보를 다시 확인해주세요.')
                logger.error("Form validation failed")
        else:
            logger.info("Processing GET request")
            user_form = UserUpdateForm(instance=user)
            profile_form = UserProfileForm(instance=profile)
        
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
        }
        
        return render(request, 'accounts/profile_edit.html', context)
        
    except Exception as e:
        logger.error(f"Exception in profile_edit: {str(e)}", exc_info=True)
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
        return redirect('dashboard')

@login_required
def remove_avatar(request):
    """프로필 이미지 삭제"""
    from django.http import JsonResponse
    if request.method == 'POST':
        try:
            profile = request.user.profile
            if profile.avatar:
                # 파일 삭제
                profile.avatar.delete()
                profile.save()
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'error': '삭제할 이미지가 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def profile_view(request):
    """사용자 프로필 보기"""
    user = request.user
    
    # UserProfile이 없으면 생성
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'accounts/profile_view.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def user_create(request):
    """사용자 생성"""
    if request.method == 'POST':
        form = UserCreationFormWithProfile(request.POST)
        if form.is_valid():
            user = form.save()
            # 새 사용자는 첫 로그인 상태로 설정
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.is_first_login = True
            profile.save()
            
            messages.success(request, f'사용자 "{user.username}"이 성공적으로 생성되었습니다.')
            
            link = request.build_absolute_uri(reverse('login'))
            send_kakao_message(
                user.email, 
                f'{profile.display_name}님의 ITMS계정이 성공적으로 생성되었습니다.\n\n ID: {user.username}\n 초기패스워드 : 123456!@ \n * 첫 로그인 후 비밀번호 변경 바랍니다.', 
                "box", 
                "바로가기", 
                link)

            return redirect('user_list')
    else:
        form = UserCreationFormWithProfile()
    
    context = {
        'form': form,
        'title': '새 사용자 생성',
    }
    
    return render(request, 'accounts/user_create.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def user_list(request):
    """사용자 목록"""
    search_query = request.GET.get('search', '')
    team_filter = request.GET.get('team', '')
    
    users = User.objects.select_related('profile').prefetch_related('teams', 'groups')
    
    # 검색 필터
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__last_name_ko__icontains=search_query) |
            Q(profile__first_name_ko__icontains=search_query)
        )
    
    # 팀 필터
    if team_filter:
        users = users.filter(teams__id=team_filter)
    
    # 페이지네이션
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 필터 옵션을 위한 데이터
    teams = Team.objects.all()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'team_filter': team_filter,
        'teams': teams,
        'title': '사용자 관리',
    }
    
    return render(request, 'accounts/user_list.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def user_detail(request, user_id):
    """사용자 상세 정보"""
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # 사용자의 팀 멤버십 정보
    team_memberships = TeamMembership.objects.filter(user=user).select_related('team')
    
    context = {
        'user': user,
        'profile': profile,
        'team_memberships': team_memberships,
        'title': f'{profile.display_name} 상세 정보',
    }
    
    return render(request, 'accounts/user_detail.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def user_edit(request, user_id):
    """사용자 정보 수정"""
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            # 팀 정보 및 역할 업데이트
            selected_team_ids = request.POST.getlist('teams')
            
            # 현재 사용자의 모든 팀 멤버십 조회
            current_memberships = TeamMembership.objects.filter(user=user)
            current_team_ids = set(current_memberships.values_list('team_id', flat=True))
            selected_team_ids = set(map(int, selected_team_ids))

            # 삭제할 멤버십 (선택 해제된 팀)
            teams_to_remove = current_team_ids - selected_team_ids
            TeamMembership.objects.filter(user=user, team_id__in=teams_to_remove).delete()

            # 추가 또는 업데이트할 멤버십
            for team_id in selected_team_ids:
                role = request.POST.get(f'team_role_{team_id}', 'member')
                TeamMembership.objects.update_or_create(
                    user=user,
                    team_id=team_id,
                    defaults={'role': role}
                )

            # 권한 그룹 업데이트
            selected_groups = request.POST.getlist('groups')
            user.groups.set(selected_groups)
            
            messages.success(request, f'사용자 "{user.username}" 정보가 성공적으로 업데이트되었습니다.')
            return redirect('user_detail', user_id=user.id)
        else:
            # 폼 유효성 검사 실패 시
            messages.error(request, '입력된 정보를 다시 확인해주세요.')

    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    # 모든 팀과 현재 사용자의 멤버십 정보를 가져옴
    all_teams = Team.objects.all().order_by('name')
    user_memberships = {tm.team_id: tm for tm in TeamMembership.objects.filter(user=user)}
    
    # 템플릿에 전달할 팀 목록 구성
    teams_data = []
    for team in all_teams:
        membership = user_memberships.get(team.id)
        teams_data.append({
            'team': team,
            'is_member': membership is not None,
            'role': membership.role if membership else 'member'
        })

    context = {
        'user_form': user_form,
        'form': profile_form,
        'user': user,
        'profile': profile,
        'teams_data': teams_data, # 팀 및 역할 정보 전달
        'role_choices': TeamMembership.ROLE_CHOICES, # 역할 선택지
        'title': f'{profile.display_name} 정보 수정',
    }
    
    return render(request, 'accounts/user_edit.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def user_delete(request, user_id):
    """사용자 삭제"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'사용자 "{username}"이 성공적으로 삭제되었습니다.')
        return redirect('user_list')
    
    context = {
        'user': user,
        'title': '사용자 삭제 확인',
    }
    
    return render(request, 'accounts/user_delete.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def team_create_ajax(request):
    """AJAX로 팀 생성"""
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.save()
            
            return JsonResponse({
                'success': True,
                'team_id': team.id,
                'team_name': team.name,
                'message': f'팀 "{team.name}"이 성공적으로 생성되었습니다.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_staff_or_superuser)
def user_team_manage(request, user_id):
    """사용자 팀 관리"""
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_team':
            team_id = request.POST.get('team_id')
            role = request.POST.get('role', 'member')
            
            if team_id:
                team = get_object_or_404(Team, id=team_id)
                membership, created = TeamMembership.objects.get_or_create(
                    team=team,
                    user=user,
                    defaults={'role': role}
                )
                
                if created:
                    messages.success(request, f'{user.username}을(를) {team.name} 팀에 추가했습니다.')
                else:
                    membership.role = role
                    membership.save()
                    messages.info(request, f'{user.username}의 {team.name} 팀 역할을 {role}로 변경했습니다.')
        
        elif action == 'remove_team':
            membership_id = request.POST.get('membership_id')
            if membership_id:
                membership = get_object_or_404(TeamMembership, id=membership_id, user=user)
                team_name = membership.team.name
                membership.delete()
                messages.success(request, f'{user.username}을(를) {team_name} 팀에서 제거했습니다.')
        
        return redirect('user_team_manage', user_id=user.id)
    
    # 사용자의 현재 팀 멤버십
    current_memberships = TeamMembership.objects.filter(user=user).select_related('team')
    current_team_ids = current_memberships.values_list('team_id', flat=True)
    
    # 가입 가능한 팀 (현재 소속되지 않은 팀)
    available_teams = Team.objects.exclude(id__in=current_team_ids)
    
    context = {
        'user': user,
        'profile': profile,
        'current_memberships': current_memberships,
        'available_teams': available_teams,
        'role_choices': TeamMembership.ROLE_CHOICES,
        'title': f'{profile.display_name} 팀 관리',
    }
    
    return render(request, 'accounts/user_team_manage.html', context)
@login_required
def user_search_ajax(request):
    """AJAX로 사용자 검색"""
    query = request.GET.get('q', '')
    team_id = request.GET.get('team_id')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    users = User.objects.select_related('profile').all()
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__last_name_ko__icontains=query) |
            Q(profile__first_name_ko__icontains=query)
        ).distinct()
        
    if team_id:
        users = users.filter(teams__id=team_id)
        
    users = users.order_by('profile__last_name_ko', 'profile__first_name_ko', 'username')
    
    paginator = Paginator(users, page_size)
    try:
        page_obj = paginator.get_page(page)
    except:
        return JsonResponse({'success': False, 'message': 'Invalid page'})
        
    user_list = []
    for u in page_obj:
        avatar_url = u.profile.avatar.url if u.profile.avatar else None
        user_list.append({
            'id': u.id,
            'username': u.username,
            'name': u.profile.get_korean_name if hasattr(u, 'profile') else u.username,
            'position': u.profile.position if hasattr(u, 'profile') else '',
            'avatar_url': avatar_url,
        })
        
    return JsonResponse({
        'success': True,
        'users': user_list,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
    })
