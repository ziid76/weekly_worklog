import subprocess
import sys
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
import os

@staff_member_required
def batch_operations(request):
    """일괄작업 메인 페이지"""
    return render(request, 'batch/operations.html')

@staff_member_required
def send_review_notifications(request):
    """리뷰 알림 발송 실행"""
    if request.method == 'POST':
        try:
            # --- 환경 변수 진단 코드 시작 ---
            aws_region = os.environ.get('AWS_SES_REGION_NAME', 'Not Set')
            aws_access_key = os.environ.get('AWS_SES_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SES_SECRET_ACCESS_KEY')

            debug_log = "[환경 변수 진단]\n"
            debug_log += f"AWS_SES_REGION_NAME: {aws_region}\n"
            debug_log += f"AWS_SES_ACCESS_KEY_ID: {'Set' if aws_access_key else 'Not Set'}\n"
            debug_log += f"AWS_SES_SECRET_ACCESS_KEY: {'Set' if aws_secret_key else 'Not Set'}\n"
            debug_log += "-"*20 + "\n\n"
            # --- 환경 변수 진단 코드 끝 ---

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # stderr를 stdout으로 리디렉션하여 모든 출력을 한 번에 캡처
            result = subprocess.run(
                [sys.executable, 'manage.py', 'send_review_notifications'],
                cwd=project_root,
                stdout=subprocess.PIPE, # stdout을 파이프로 캡처
                stderr=subprocess.STDOUT, # stderr를 stdout으로 리디렉션
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            # 진단 로그와 명령어 실행 결과를 합쳐서 전달
            full_output = debug_log + result.stdout

            return JsonResponse({
                'success': result.returncode == 0,
                'stdout': full_output,
                'stderr': '',  # stdout으로 통합되었으므로 비워둠
                'returncode': result.returncode
            })
            
        except subprocess.TimeoutExpired as e:
            return JsonResponse({
                'success': False,
                'error': '명령어 실행 시간이 초과되었습니다 (5분)',
                'stdout': f"Timeout after {e.timeout} seconds.",
                'stderr': ''
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': ''
            })
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다'}, status=405)

@staff_member_required
def generate_missing_reviews(request):
    """누락된 리뷰 생성 실행"""
    if request.method == 'POST':
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            result = subprocess.run(
                [sys.executable, 'manage.py', 'generate_missing_reviews'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )
            
            return JsonResponse({
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
            
        except subprocess.TimeoutExpired:
            return JsonResponse({
                'success': False,
                'error': '명령어 실행 시간이 초과되었습니다 (10분)',
                'stdout': '',
                'stderr': ''
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': ''
            })
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다'}, status=405)

@staff_member_required
def check_monitor_notifications(request):
    """모니터링 알림 확인 실행"""
    if request.method == 'POST':
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            result = subprocess.run(
                [sys.executable, 'manage.py', 'check_notifications', '--type=monitor'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            return JsonResponse({
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
            
        except subprocess.TimeoutExpired:
            return JsonResponse({
                'success': False,
                'error': '명령어 실행 시간이 초과되었습니다 (5분)',
                'stdout': '',
                'stderr': ''
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': ''
            })
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다'}, status=405)
