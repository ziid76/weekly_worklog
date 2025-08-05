from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from collections import defaultdict
import datetime
from django.http import JsonResponse
from .models import WeeklyReport, WeeklyReportComment, TeamWeeklyReport
from worklog.models import Worklog
from teams.models import Team, TeamMembership
from .forms import WeeklyReportCommentForm, TeamWeeklyReportForm

class WeeklyReportListView(LoginRequiredMixin, ListView, ):
    model = WeeklyReport
    template_name = 'reports/weekly_report_list.html'
    context_object_name = 'reports'
    paginate_by = 10

    def get_queryset(self):
        return WeeklyReport.objects.filter(team=self.request.user.profile.primary_team.id).order_by('-year', '-week_number')

@login_required
def weekly_report_detail(request, id):
    """주간 리포트 상세 보기"""
    team_id = request.user.profile.primary_team.id
    print(team_id)
    report = get_object_or_404(WeeklyReport, id=id)
    
    
    # 팀이 지정된 경우 해당 팀의 워크로그만, 아니면 전체
    if report.team:
        team = get_object_or_404(Team, id=report.team.id)
        # 팀 멤버들의 워크로그만 가져오기
        team_members = team.members.all()
        worklogs = Worklog.objects.filter(
            year=report.year, 
            week_number=report.week_number,
            author__in=team_members
        ).select_related('author')
        

    else:
        # 전체 워크로그
        worklogs = Worklog.objects.filter(year=report.year, week_number=report.week_number).select_related('author')

    
    # 댓글 처리
    if request.method == 'POST':
        form = WeeklyReportCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.report = report
            comment.author = request.user
            comment.save()
            messages.success(request, '코멘트가 추가되었습니다.')
            return redirect('weekly_report_detail', id=report.id)
    else:
        form = WeeklyReportCommentForm()
    
    # 작성자별 워크로그 그룹화
    worklog_by_author = {}
    for worklog in worklogs:
        # UserProfile이 있으면 한국식 이름 사용, 없으면 username 사용
        try:
            author_name = worklog.author.profile.get_korean_name
        except:
            author_name = worklog.author.username
        
        worklog_by_author[author_name] = worklog
    
    context = {
        'report': report,
        'worklogs': worklogs,
        'worklog_by_author': worklog_by_author,
        'form': form,
        'comments': report.comments.all(),
        'year': report.year,
        'week_number': report.week_number,
        'selected_team': report.team,
    }
    print(report.team)
    
    return render(request, 'reports/weekly_report_detail.html', context)

@login_required
def generate_weekly_report(request):
    """주간 리포트 생성 및 최근 5주 현황 페이지"""


    team = get_object_or_404(Team, id=request.user.profile.primary_team.id)
    team_members = team.members.all()
    
    if request.method == 'POST':
        year = int(request.POST.get('year'))
        week_number = int(request.POST.get('week_number'))

        week_start = datetime.date.fromisocalendar(year, week_number, 1)
        month_week_display = f"{week_start.month}월 {((week_start.day - 1) // 7) + 1}주차"
        
        # 팀 ID는 이제 사용하지 않으므로 team=None으로 고정
        report, created = WeeklyReport.objects.get_or_create(
            year=year,
            week_number=week_number,
            team=team,
            defaults={
                'title': f'{month_week_display} {team.name} 주간보고서',
                'created_by': request.user
            }
        )
        
        if created:
            messages.success(request, f'{month_week_display} {team.name} 주간보고서가 생성되었습니다.')
        
        return redirect('weekly_report_detail', id=report.id)

    # --- 최근 5주 데이터 생성 ---
    today = datetime.date.today()
    recent_weeks = []

    for i in range(5):
        target_date = today - datetime.timedelta(weeks=i)
        year, week_number, _ = target_date.isocalendar()
        
        # 해당 주의 첫 날과 마지막 날 계산
        week_start = datetime.date.fromisocalendar(year, week_number, 1)
        
        # "M월 W주차" 형식 생성
        month_week_display = f"{week_start.month}월 {((week_start.day - 1) // 7) + 1}주차"



        # 해당 주차의 Worklog 개수 계산
        worklog_count = Worklog.objects.filter(year=year, week_number=week_number, author__in=team_members).count()
        
        # 이미 생성된 리포트가 있는지 확인 (팀 없는 전체 리포트 기준)
        report = WeeklyReport.objects.filter(year=year, week_number=week_number, team=team).first()

        recent_weeks.append({
            'year': year,
            'week_number': week_number,
            'month_week_display': month_week_display,
            'worklog_count': worklog_count,
            'report': report,
        })

    context = {
        'recent_weeks': recent_weeks,
    }
    
    return render(request, 'reports/generate_weekly_report.html', context)

@login_required
def team_worklog_summary(request):
    """팀별 워크로그 요약"""
    year = request.GET.get('year')
    week_number = request.GET.get('week_number')
    team_id = request.GET.get('team')
    
    if not year or not week_number:
        today = datetime.date.today()
        year, week_number, _ = today.isocalendar()
    else:
        year = int(year)
        week_number = int(week_number)
    
    # 팀별로 워크로그 필터링
    if team_id:
        team = get_object_or_404(Team, id=team_id)
        team_members = team.members.all()
        worklogs = Worklog.objects.filter(
            year=year, 
            week_number=week_number,
            author__in=team_members
        ).select_related('author')
        selected_team = team
    else:
        worklogs = Worklog.objects.filter(
            year=year, 
            week_number=week_number
        ).select_related('author')
        selected_team = None
    
    # 팀별로 그룹화 (실제 팀 멤버십 기준)
    team_summary = defaultdict(list)
    
    for worklog in worklogs:
        try:
            author_name = worklog.author.profile.get_korean_name
        except:
            author_name = worklog.author.username
        
        # 사용자의 팀 정보 가져오기
        user_teams = TeamMembership.objects.filter(user=worklog.author).select_related('team')
        
        if user_teams.exists():
            for membership in user_teams:
                team_summary[membership.team.name].append({
                    'author': author_name,
                    'worklog': worklog,
                    'role': membership.get_role_display()
                })
        else:
            team_summary['미분류'].append({
                'author': author_name,
                'worklog': worklog,
                'role': '일반'
            })
    
    # 연도 및 주차 선택 옵션
    current_year = datetime.date.today().year
    year_choices = list(range(current_year - 2, current_year + 3))
    week_choices = list(range(1, 54))
    
    # 팀 목록
    teams = Team.objects.all()
    
    context = {
        'year': year,
        'week_number': week_number,
        'team_summary': dict(team_summary),
        'week_start': datetime.date.fromisocalendar(year, week_number, 1),
        'week_end': datetime.date.fromisocalendar(year, week_number, 1) + datetime.timedelta(days=6),
        'year_choices': year_choices,
        'week_choices': week_choices,
        'teams': teams,
        'selected_team': selected_team,
    }
    
    return render(request, 'reports/team_worklog_summary.html', context)

@login_required
def worklog_summary_popup(request, year, week_number):
    """작성자별 워크로그 집계 팝업"""
    team_id = request.GET.get('team')
    
    # 팀이 지정된 경우 해당 팀의 워크로그만, 아니면 전체
    if team_id:
        team = get_object_or_404(Team, id=team_id)
        # 팀 멤버들의 워크로그만 가져오기
        team_members = team.members.all()
        worklogs = Worklog.objects.filter(
            year=year, 
            week_number=week_number,
            author__in=team_members
        ).select_related('author')
        
        report = get_object_or_404(WeeklyReport, year=year, week_number=week_number, team=team)
    else:
        # 전체 워크로그
        worklogs = Worklog.objects.filter(year=year, week_number=week_number).select_related('author')
        report = get_object_or_404(WeeklyReport, year=year, week_number=week_number, team=None)
    
    # 작성자별 워크로그 그룹화
    worklog_by_author = {}
    for worklog in worklogs:
        # UserProfile이 있으면 한국식 이름 사용, 없으면 username 사용
        try:
            author_name = worklog.author.profile.get_korean_name
        except:
            author_name = worklog.author.username
        
        worklog_by_author[author_name] = worklog
    
    context = {
        'report': report,
        'worklog_by_author': worklog_by_author,
    }
    
    return render(request, 'reports/worklog_summary_popup.html', context)

@login_required
def confirm_closing_api(request):
    try:
        report = get_object_or_404(WeeklyReport, pk=request.POST.get('pk'))
        report.editable = False
        report.save()

        return JsonResponse({
            'success': True,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
