import datetime
import logging
import os
import subprocess
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render

from reports.models import ReportReview, TeamPerformanceAnalysis
from teams.models import Team

logger = logging.getLogger(__name__)


def _get_month_week_label(week_start: datetime.date, week_end: datetime.date) -> str:
    if week_start.month == week_end.month:
        first_monday = week_start.replace(day=1)
        while first_monday.weekday() != 0:
            first_monday += datetime.timedelta(days=1)
        week_index = (week_start - first_monday).days // 7 + 1
        return f"{week_start.month}월 {week_index}주차"

    month_base = week_end if week_start.day <= 3 else week_start
    first_monday = month_base.replace(day=1)
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(days=1)
    week_index = (month_base - first_monday).days // 7 + 1
    return f"{month_base.month}월 {week_index}주차"


def _get_recent_week_options(count: int = 5):
    today = datetime.date.today()
    this_monday = today - datetime.timedelta(days=today.weekday())
    options = []

    for i in range(count):
        week_start = this_monday - datetime.timedelta(weeks=i)
        week_end = week_start + datetime.timedelta(days=6)
        year, week_number, _ = week_start.isocalendar()
        month_week = _get_month_week_label(week_start, week_end)
        options.append(
            {
                'value': f'{year}-{week_number}',
                'label': f'{month_week}({week_start.month}/{week_start.day}~{week_end.month}/{week_end.day})',
            }
        )

    return options


def _parse_week_value(week_value: str):
    if not week_value:
        return None

    try:
        year_str, week_str = week_value.split('-', 1)
        year = int(year_str)
        week = int(week_str)
        datetime.date.fromisocalendar(year, week, 1)
        return year, week
    except (TypeError, ValueError):
        return None


def _format_week_str(year: int, week: int) -> str:
    return f"{year}-W{week}"


def _get_review_completion_status(year: int, week_number: int):
    target_users = User.objects.filter(
        teams__isnull=False,
        worklogs__year=year,
        worklogs__week_number=week_number,
    ).distinct()
    target_count = target_users.count()

    reviewed_count = ReportReview.objects.filter(
        user__in=target_users,
        year=year,
        week_number=week_number,
    ).values('user_id').distinct().count()

    pending_count = max(target_count - reviewed_count, 0)
    completed = pending_count == 0

    return {
        'completed': completed,
        'target_count': target_count,
        'reviewed_count': reviewed_count,
        'pending_count': pending_count,
        'can_run': not completed,
        'label': '완료' if completed else '미완료',
    }


def _get_team_performance_status(team_id: str, year: int, week_number: int):
    if not team_id:
        return {
            'completed': False,
            'can_run': False,
            'label': '팀 선택 필요',
            'exists': False,
        }

    try:
        team_id_int = int(team_id)
        anchor_monday = datetime.date.fromisocalendar(year, week_number, 1)
    except (TypeError, ValueError):
        return {
            'completed': False,
            'can_run': False,
            'label': '미완료',
            'exists': False,
        }

    start_monday = anchor_monday - datetime.timedelta(weeks=3)
    start_year, start_week, _ = start_monday.isocalendar()
    end_year, end_week, _ = anchor_monday.isocalendar()

    start_week_str = _format_week_str(start_year, start_week)
    end_week_str = _format_week_str(end_year, end_week)

    exists = TeamPerformanceAnalysis.objects.filter(
        team_id=team_id_int,
        start_week=start_week_str,
        end_week=end_week_str,
    ).exists()

    return {
        'completed': exists,
        'can_run': not exists,
        'label': '완료' if exists else '미완료',
        'exists': exists,
        'start_week': start_week_str,
        'end_week': end_week_str,
    }


@staff_member_required
def batch_operations(request):
    teams = Team.objects.all().order_by('name')
    week_options = _get_recent_week_options()
    return render(
        request,
        'batch/operations.html',
        {
            'teams': teams,
            'week_options': week_options,
            'default_week_value': week_options[0]['value'] if week_options else '',
        },
    )


@staff_member_required
def send_review_notifications(request):
    if request.method == 'POST':
        try:
            aws_region = os.environ.get('AWS_SES_REGION_NAME', 'Not Set')
            aws_access_key = os.environ.get('AWS_SES_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SES_SECRET_ACCESS_KEY')

            debug_log = "[ENV CHECK]\n"
            debug_log += f"AWS_SES_REGION_NAME: {aws_region}\n"
            debug_log += f"AWS_SES_ACCESS_KEY_ID: {'Set' if aws_access_key else 'Not Set'}\n"
            debug_log += f"AWS_SES_SECRET_ACCESS_KEY: {'Set' if aws_secret_key else 'Not Set'}\n"
            debug_log += "-" * 20 + "\n\n"

            logger.info("Starting send_review_notifications batch job.")
            logger.debug(debug_log)

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run(
                [sys.executable, 'manage.py', 'send_review_notifications'],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=300,
            )

            full_output = debug_log + result.stdout

            logger.info(f"Batch job finished with return code {result.returncode}")
            logger.info(f"Output:\n{full_output}")
            logger.debug(f"Output:\n{full_output}")

            return JsonResponse(
                {
                    'success': result.returncode == 0,
                    'stdout': full_output,
                    'stderr': '',
                    'returncode': result.returncode,
                }
            )

        except subprocess.TimeoutExpired as e:
            logger.error(f"Batch job timed out: {e}")
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Command execution timed out (5 minutes).',
                    'stdout': f"Timeout after {e.timeout} seconds.",
                    'stderr': '',
                }
            )
        except Exception as e:
            logger.error(f"Batch job failed with exception: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e), 'stdout': '', 'stderr': ''})

    return JsonResponse({'error': 'POST request only allowed.'}, status=405)


@staff_member_required
def generate_missing_reviews(request):
    if request.method == 'POST':
        try:
            week_value = request.POST.get('week')
            parsed_week = _parse_week_value(week_value)
            if not parsed_week:
                return JsonResponse({'success': False, 'error': 'Invalid week selection.'})
            year, week_number = parsed_week

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run(
                [
                    sys.executable,
                    'manage.py',
                    'generate_missing_reviews',
                    '--year',
                    str(year),
                    '--week',
                    str(week_number),
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            logger.info("Starting generate_missing_reviews batch job.")
            logger.info(f"Batch job finished with return code {result.returncode}")
            if result.stdout:
                logger.info(f"Stdout:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Stderr:\n{result.stderr}")

            return JsonResponse(
                {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode,
                }
            )

        except subprocess.TimeoutExpired as e:
            logger.error(f"Batch job timed out: {e}")
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Command execution timed out (10 minutes).',
                    'stdout': '',
                    'stderr': '',
                }
            )
        except Exception as e:
            logger.error(f"Batch job failed with exception: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e), 'stdout': '', 'stderr': ''})

    return JsonResponse({'error': 'POST request only allowed.'}, status=405)


@staff_member_required
def check_monitor_notifications(request):
    if request.method == 'POST':
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            result = subprocess.run(
                [sys.executable, 'manage.py', 'check_notifications', '--type=monitor'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            logger.info("Starting check_monitor_notifications batch job.")
            logger.info(f"Batch job finished with return code {result.returncode}")
            if result.stdout:
                logger.info(f"Stdout:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Stderr:\n{result.stderr}")

            return JsonResponse(
                {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode,
                }
            )

        except subprocess.TimeoutExpired as e:
            logger.error(f"Batch job timed out: {e}")
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Command execution timed out (5 minutes).',
                    'stdout': '',
                    'stderr': '',
                }
            )
        except Exception as e:
            logger.error(f"Batch job failed with exception: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e), 'stdout': '', 'stderr': ''})

    return JsonResponse({'error': 'POST request only allowed.'}, status=405)


@staff_member_required
def analyze_team_performance(request):
    if request.method == 'POST':
        try:
            team_id = request.POST.get('team_id')
            if not team_id:
                return JsonResponse({'success': False, 'error': 'Team ID is required.'})

            week_value = request.POST.get('week')
            parsed_week = _parse_week_value(week_value)
            if not parsed_week:
                return JsonResponse({'success': False, 'error': 'Invalid week selection.'})
            year, week_number = parsed_week

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run(
                [
                    sys.executable,
                    'manage.py',
                    'analyze_team_performance',
                    str(team_id),
                    '--year',
                    str(year),
                    '--week',
                    str(week_number),
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            logger.info(f"Starting analyze_team_performance batch job for Team ID {team_id}.")
            logger.info(f"Batch job finished with return code {result.returncode}")
            if result.stdout:
                logger.info(f"Stdout:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Stderr:\n{result.stderr}")

            return JsonResponse(
                {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode,
                }
            )

        except subprocess.TimeoutExpired as e:
            logger.error(f"Batch job timed out: {e}")
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Command execution timed out (5 minutes).',
                    'stdout': '',
                    'stderr': '',
                }
            )
        except Exception as e:
            logger.error(f"Batch job failed with exception: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e), 'stdout': '', 'stderr': ''})

    return JsonResponse({'error': 'POST request only allowed.'}, status=405)


@staff_member_required
def get_operation_status(request):
    review_week = request.GET.get('review_week') or request.GET.get('week') or request.GET.get('performance_week')
    performance_week = request.GET.get('performance_week') or request.GET.get('week') or request.GET.get('review_week')
    team_id = request.GET.get('team_id')

    review_parsed = _parse_week_value(review_week)
    performance_parsed = _parse_week_value(performance_week)

    if not review_parsed or not performance_parsed:
        return JsonResponse({'success': False, 'error': 'Invalid week selection.'}, status=400)

    review_year, review_week_number = review_parsed
    perf_year, perf_week_number = performance_parsed

    review_status = _get_review_completion_status(review_year, review_week_number)
    performance_status = _get_team_performance_status(team_id, perf_year, perf_week_number)

    return JsonResponse(
        {
            'success': True,
            'review': review_status,
            'performance': performance_status,
        }
    )


@staff_member_required
def get_batch_logs(request):
    try:
        log_file_path = os.path.join(settings.BASE_DIR, 'logs', 'batch.log')
        if not os.path.exists(log_file_path):
            return JsonResponse({'success': False, 'message': 'Log file not found.'})

        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return JsonResponse({'success': True, 'content': content})
    except Exception as e:
        logger.error(f"Failed to read batch logs: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)})
