from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from collections import defaultdict
import datetime
import re
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from .models import WeeklyReport, WeeklyReportComment, TeamWeeklyReport, WeeklyReportPersonalComment
from worklog.models import Worklog
from teams.models import Team, TeamMembership
from accounts.models import UserProfile
from django.contrib.auth.models import User
from .forms import WeeklyReportCommentForm, TeamWeeklyReportForm, WeeklyReportPersonalCommentForm
import html
from django.utils.html import strip_tags
from django.template.loader import render_to_string

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
        ).select_related('author', 'author__profile').order_by('display_order', 'author__profile__last_name_ko', 'author__username')
        

    else:
        # 전체 워크로그
        worklogs = Worklog.objects.filter(
            year=report.year, 
            week_number=report.week_number
        ).select_related('author', 'author__profile').order_by('display_order', 'author__profile__last_name_ko', 'author__username')

    
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

    personal_comment_form = WeeklyReportPersonalCommentForm()

    # 작성자별 워크로그 및 업무 코멘트 그룹화
    personal_comments = report.personal_comments.select_related(
        'target_user__profile',
        'created_by__profile'
    ).order_by('created_at')

    comments_by_user = defaultdict(list)
    for comment in personal_comments:
        comments_by_user[comment.target_user_id].append(comment)

    worklog_entries = []
    for worklog in worklogs:
        author_profile = getattr(worklog.author, 'profile', None)
        author_name = author_profile.get_korean_name if author_profile else worklog.author.username

        worklog_entries.append({
            'author': worklog.author,
            'author_id': worklog.author_id,
            'author_name': author_name,
            'worklog': worklog,
            'personal_comments': comments_by_user.get(worklog.author_id, []),
        })

    user_role = None
    if hasattr(request.user, 'profile'):
        user_role = request.user.profile.current_team_role

    can_manage_personal_comments = request.user.is_staff or request.user.is_superuser or user_role in ('leader', 'admin')

    context = {
        'report': report,
        'worklogs': worklogs,
        'worklog_entries': worklog_entries,
        'worklog_count': len(worklog_entries),
        'form': form,
        'comments': report.comments.select_related('author__profile').all(),
        'personal_comment_form': personal_comment_form,
        'can_manage_personal_comments': can_manage_personal_comments,
        'year': report.year,
        'week_number': report.week_number,
        'selected_team': report.team,
    }
    return render(request, 'reports/weekly_report_detail.html', context)


@login_required
def add_personal_comment(request, report_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=405)

    report = get_object_or_404(WeeklyReport, id=report_id)

    user_role = None
    if hasattr(request.user, 'profile'):
        user_role = request.user.profile.current_team_role

    if not (request.user.is_staff or request.user.is_superuser or user_role in ('leader', 'admin')):
        return JsonResponse({'success': False, 'error': '업무 코멘트를 작성할 권한이 없습니다.'}, status=403)

    target_user_id = request.POST.get('target_user_id')
    if not target_user_id:
        return JsonResponse({'success': False, 'error': '대상 사용자가 지정되지 않았습니다.'}, status=400)

    target_user = get_object_or_404(User, id=target_user_id)

    if not Worklog.objects.filter(
        year=report.year,
        week_number=report.week_number,
        author=target_user
    ).exists():
        return JsonResponse({'success': False, 'error': '해당 사용자의 주간업무가 존재하지 않습니다.'}, status=400)

    form = WeeklyReportPersonalCommentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'error': '코멘트 내용을 입력해주세요.'}, status=400)

    personal_comment = form.save(commit=False)
    personal_comment.report = report
    personal_comment.target_user = target_user
    personal_comment.created_by = request.user
    personal_comment.save()

    updated_comments = report.personal_comments.filter(
        target_user=target_user
    ).select_related('created_by__profile').order_by('created_at')

    comments_html = render_to_string(
        'reports/partials/personal_comment_list.html',
        {'comments': updated_comments},
        request=request
    )

    return JsonResponse({
        'success': True,
        'html': comments_html,
        'target_user_id': target_user_id,
    })

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
        ).select_related('author', 'author__profile').order_by('display_order', 'author__profile__last_name_ko', 'author__username')
        
        report = get_object_or_404(WeeklyReport, year=year, week_number=week_number, team=team)
    else:
        # 전체 워크로그
        worklogs = Worklog.objects.filter(
            year=year, 
            week_number=week_number
        ).select_related('author', 'author__profile').order_by('display_order', 'author__profile__last_name_ko', 'author__username')
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

@login_required
def export_weekly_report_excel(request, id):
    """주간 리포트 Excel 내보내기"""
    report = get_object_or_404(WeeklyReport, id=id)
    
    # 워크로그 데이터 가져오기
    worklogs = Worklog.objects.filter(
        year=report.year,
        week_number=report.week_number,
        author__teams=report.team
    ).select_related('author', 'author__profile').order_by('display_order', 'author__profile__last_name_ko', 'author__username')
    
    worklog_by_author = {}
    for worklog in worklogs:
        author_name = worklog.author.profile.display_name if worklog.author.profile else worklog.author.username
        worklog_by_author[author_name] = worklog
    
    # Excel 워크북 생성
    wb = Workbook()
    ws = wb.active
    ws.title = f"{report.year}년 {report.week_number}주차 주간보고서"
    
    # 스타일 정의
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 헤더 작성
    ws['A1'] = "담당자"
    ws['B1'] = f"금주 실적 ({report.week_start_date.strftime('%m월 %d일')} ~ {report.week_end_date.strftime('%m월 %d일')})"
    ws['C1'] = f"차주 계획 ({report.next_week_start_date.strftime('%m월 %d일')} ~ {report.next_week_end_date.strftime('%m월 %d일')})"
    
    # 헤더 스타일 적용
    for col in ['A1', 'B1', 'C1']:
        ws[col].font = header_font
        ws[col].fill = header_fill
        ws[col].alignment = Alignment(horizontal='center', vertical='center')
        ws[col].border = border
    
    # 컬럼 너비 설정
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 50
    ws.column_dimensions['C'].width = 50
    
    # 데이터 작성
    row = 2
    for author_name, worklog in worklog_by_author.items():
        ws[f'A{row}'] = author_name
        
        # 마크다운 텍스트를 일반 텍스트로 변환
        this_week_text = clean_markdown_text(worklog.this_week_work) if worklog.this_week_work else "작성된 내용이 없습니다."
        next_week_text = clean_markdown_text(worklog.next_week_plan) if worklog.next_week_plan else "작성된 계획이 없습니다."
        
        ws[f'B{row}'] = this_week_text
        ws[f'C{row}'] = next_week_text
        
        # 셀 스타일 적용
        for col in ['A', 'B', 'C']:
            cell = ws[f'{col}{row}']
            cell.border = border
            cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        
        row += 1
    
    # HTTP 응답 생성
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # 팀명과 월/주차 정보로 파일명 생성
    team_name = report.team.name if report.team else "전체"
    month = report.week_start_date.month
    week_in_month = ((report.week_start_date.day - 1) // 7) + 1
    filename = f"{team_name}_주간보고서_{month}월_{week_in_month}주차.xlsx"
    
    # 파일명 인코딩 처리 (한글 및 특수문자 지원)
    from urllib.parse import quote
    encoded_filename = quote(filename.encode('utf-8'))
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    
    wb.save(response)
    return response

def clean_markdown_text(text):
    """마크다운 및 HTML 텍스트를 일반 텍스트로 변환"""
    if not text:
        return ""

    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r'</p\s*>', '\n', text, flags=re.IGNORECASE)

    # HTML 태그 제거
    text = strip_tags(text)
    
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    
    # 마크다운 문법 제거
    text = re.sub(r'#{1,6}\s*', '', text)  # 헤더
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 굵은 글씨
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # 기울임
    text = re.sub(r'`(.*?)`', r'\1', text)  # 인라인 코드
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)  # 리스트
    text = re.sub(r'^\s*\d+\.\s+', '• ', text, flags=re.MULTILINE)  # 번호 리스트
    
    # 연속된 공백과 줄바꿈 정리
    text = re.sub(r'\n\s*\n', '\n', text)  # 빈 줄 제거
    text = re.sub(r' +', ' ', text)  # 연속 공백 제거
    
    return text.strip()

import json

@login_required
def personal_report_history(request):
    """ 개인별 주간업무 이력 조회 """
    # 현재 로그인한 유저의 팀 정보 가져오기
    try:
        primary_team = request.user.profile.primary_team
        team_members = User.objects.filter(teams=primary_team).select_related('profile').order_by('profile__last_name_ko', 'profile__first_name_ko')
    except AttributeError:
        # 팀 정보가 없는 경우 (예: 관리자)
        primary_team = None
        team_members = User.objects.all().select_related('profile').order_by('profile__last_name_ko', 'profile__first_name_ko')

    # 필터링 파라미터
    selected_user_id = request.GET.get('user_id')
    
    # 날짜 기본값 설정 (최근 5주)
    today = datetime.date.today()
    end_year_default, end_week_default, _ = today.isocalendar()
    start_date_default = today - datetime.timedelta(weeks=4)
    start_year_default, start_week_default, _ = start_date_default.isocalendar()

    start_year = request.GET.get('start_year', str(start_year_default))
    start_week = request.GET.get('start_week', str(start_week_default))
    end_year = request.GET.get('end_year', str(end_year_default))
    end_week = request.GET.get('end_week', str(end_week_default))

    # 연도 선택 옵션
    current_year = datetime.date.today().year
    year_choices = list(range(current_year - 3, current_year + 1))

    # 연도별 주차 정보 생성 (for JavaScript)
    week_data = {}
    for year in year_choices:
        week_data[year] = []
        for week_num in range(1, 54):
            try:
                week_start = datetime.date.fromisocalendar(year, week_num, 1)
                # 주차의 마지막 날이 다음 해로 넘어가는 경우 방지
                if week_start.year != year and week_num > 1:
                    continue
                week_end = week_start + datetime.timedelta(days=4)
                display_text = f"{week_num}주차 ({week_start.strftime('%m.%d')}~{week_end.strftime('%m.%d')})"
                week_data[year].append({'week': week_num, 'display': display_text})
            except ValueError:
                # 53주차가 없는 해 처리
                break

    worklogs_data = []
    if selected_user_id:
        # worklog 쿼리
        worklogs = Worklog.objects.filter(
            author_id=selected_user_id,
        ).order_by('-year', '-week_number')

        # 기간 필터링
        worklogs = worklogs.filter(
            Q(year__gt=int(start_year)) |
            Q(year=int(start_year), week_number__gte=int(start_week))
        )
        worklogs = worklogs.filter(
            Q(year__lt=int(end_year)) |
            Q(year=int(end_year), week_number__lte=int(end_week))
        )

        for log in worklogs:
            # 전주 계획을 가져오기
            prev_week_date = log.week_start_date - datetime.timedelta(days=7)
            prev_year, prev_week, _ = prev_week_date.isocalendar()
            
            previous_worklog = Worklog.objects.filter(
                author_id=selected_user_id,
                year=prev_year,
                week_number=prev_week
            ).first()
            
            worklogs_data.append({
                'worklog': log,
                'previous_week_plan': previous_worklog.next_week_plan if previous_worklog else ''
            })

    context = {
        'team_members': team_members,
        'year_choices': year_choices,
        'week_data_json': json.dumps(week_data),
        'selected_user_id': selected_user_id,
        'start_year': start_year,
        'start_week': start_week,
        'end_year': end_year,
        'end_week': end_week,
        'worklogs_data': worklogs_data,
    }
    return render(request, 'reports/personal_report_history.html', context)