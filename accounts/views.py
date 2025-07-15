from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import UserProfile
from .forms import UserProfileForm, UserUpdateForm, UserCreationFormWithProfile, TeamCreationForm, UserEditForm
from teams.models import Team, TeamMembership

def is_staff_or_superuser(user):
    """관리자 권한 확인"""
    return user.is_staff or user.is_superuser

@login_required
def profile_edit(request):
    """사용자 프로필 편집"""
    user = request.user
    
    # UserProfile이 없으면 생성
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
            return redirect('profile_edit')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    
    return render(request, 'accounts/profile_edit.html', context)

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
            messages.success(request, f'사용자 "{user.username}"이 성공적으로 생성되었습니다.')
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
        form = UserEditForm(request.POST, user=user)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'사용자 "{user.username}" 정보가 성공적으로 업데이트되었습니다.')
            return redirect('user_detail', user_id=user.id)
    else:
        form = UserEditForm(user=user)
    
    context = {
        'form': form,
        'user': user,
        'profile': profile,
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
