from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from monitor.models import (
    OperationLog, OperationLogAttachment, LogCategory, 
    LogSubcategory, LogEntry, SubcategoryEntry
)
from datetime import date, datetime
from calendar import monthrange
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Prefetch

from django.views.decorators.csrf import csrf_exempt
import json


def index(request):
    return HttpResponse("Monitor 앱입니다.")


@login_required
def operation_log_list(request):
    month = request.GET.get('month')
    if not month:
        month = datetime.today().strftime('%Y-%m')
    year, mon = map(int, month.split('-'))

    logs = OperationLog.objects.filter(date__year=year, date__month=mon).order_by('date')
    
    # Get all active categories for display
    categories = LogCategory.objects.filter(is_active=True).order_by('order')
    
    # 각 로그와 카테고리에 대한 로그 항목을 미리 준비
    log_entries_map = {}
    for log in logs:
        log_entries_map[log.id] = {}
        for category in categories:
            entry = LogEntry.objects.filter(operation_log=log, category=category).first()
            log_entries_map[log.id][category.id] = entry
    
    return render(request, 'operation_log_list.html', {
        'logs': logs,
        'selected_month': month,
        'categories': categories,
        'log_entries_map': log_entries_map,
    })


@login_required
def operation_log_detail(request, pk):
    log = get_object_or_404(OperationLog, pk=pk)
    ready = log.check_complete()
    current_step = get_workflow_status(log.check_start(), log.check_complete(), log.completed, log.approved)

    steps = [
        {'name': '점검 전', 'step': -1, 'date': ' '},
        {'name': '점검 진행', 'step': 0, 'date': ' '},
        {'name': '점검 완료', 'step': 1, 'date': ''},
        {'name': '담당자 검토', 'step': 2, 'date': log.completed_at},
        {'name': '승인', 'step': 3, 'date': log.approved_at},
    ]

    for s in steps:
        if s['step'] < current_step:
            s['status'] = 'Y'
        elif s['step'] == current_step:
            s['status'] = 'P'
        else:
            s['status'] = 'N'
    
    # Get all categories and their log entries for this operation log
    categories = LogCategory.objects.filter(is_active=True).order_by('order')
    log_entries = {}
    
    for category in categories:
        entry = LogEntry.objects.filter(operation_log=log, category=category).first()
        if not entry:
            entry = None
        log_entries[category.id] = entry
    
    return render(request, 'operation_log_detail.html', {
        'log': log,
        'ready': ready,
        'steps': steps,
        'step': current_step+1,
        'categories': categories,
        'log_entries': log_entries,
    })


def get_workflow_status(check_start, check_complete, completed, approved):
    if not check_start:
        return 0
    elif not check_complete:
        return 1
    elif not completed:
        return 2
    elif not approved:
        return 3
    else:
        return 4


@login_required
def operation_log_complete(request, pk):
    log = get_object_or_404(OperationLog, pk=pk)
    if request.method == 'POST':
        if log.finalize(request.user):
            messages.info(request, '완료 처리되었습니다.')
        else:
            messages.error(request, '모든 항목을 등록해야 합니다.')
        return redirect('operation_log_detail', pk=pk)
    return redirect('operation_log_detail', pk=pk)


@user_passes_test(lambda u: u.is_staff)
@login_required
def operation_log_approval_list(request):
    logs = OperationLog.objects.filter(completed=True, approved=False).order_by('date')
    return render(request, 'operation_log_approval_list.html', {'logs': logs})


@user_passes_test(lambda u: u.is_staff)
@login_required
def operation_log_approve(request, pk):
    log = get_object_or_404(OperationLog, pk=pk)
    log.approved = True
    log.approved_at = timezone.now()
    log.approved_by = request.user
    log.save()
    messages.info(request, '승인되었습니다.')
    return redirect('operation_log_approval_list')


@login_required
def operation_log_add(request):
    if request.method == 'POST':
        log = get_object_or_404(OperationLog, pk=request.POST.get('log_id'))
        category_id = request.POST.get('category_id')
        content = request.POST.get('monitor_log', '')
        checked = bool(request.POST.get('is_checked'))
        troubled = bool(request.POST.get('has_trouble'))
        now = timezone.now()
        
        # Get or create log entry for this category
        category = get_object_or_404(LogCategory, pk=category_id)
        log_entry, created = LogEntry.objects.get_or_create(
            operation_log=log,
            category=category,
            defaults={
                'result': content,
                'is_checked': checked,
                'has_trouble': troubled,
                'checked_by': request.user,
                'checked_at': now
            }
        )
        
        if not created:
            log_entry.result = content
            log_entry.is_checked = checked
            log_entry.checked_by = request.user
            log_entry.checked_at = now
            log_entry.save()
        
        # Process subcategory entries if provided
        for key, value in request.POST.items():
            if key.startswith('subcategory_'):
                try:
                    subcategory_id = int(key.split('_')[1])
                    subcategory = get_object_or_404(LogSubcategory, pk=subcategory_id)
                    
                    # Check if this subcategory belongs to the selected category
                    if subcategory.category_id != int(category_id):
                        continue
                    
                    is_checked = bool(value)
                    result = request.POST.get(f'subcategory_result_{subcategory_id}', '')
                    
                    # Get or create subcategory entry
                    subcategory_entry, _ = SubcategoryEntry.objects.get_or_create(
                        log_entry=log_entry,
                        subcategory=subcategory,
                        defaults={
                            'result': result,
                            'is_checked': is_checked
                        }
                    )
                    
                    if not _:
                        subcategory_entry.result = result
                        subcategory_entry.is_checked = is_checked
                        subcategory_entry.save()
                except (ValueError, LogSubcategory.DoesNotExist):
                    continue
        
        # Handle file attachments
        for file_ in request.FILES.getlist('attachments'):
            OperationLogAttachment.objects.create(record=log, file=file_)

    return redirect('operation_log_list')


@login_required
def operation_duty(request):
    month = request.GET.get('month')
    if not month:
        month = datetime.today().strftime('%Y-%m')

    return render(request, 'operation_duty.html', {'selected_month': month})


@login_required
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse({'subcategories': []})
    
    try:
        category = LogCategory.objects.get(pk=category_id)
        subcategories = category.subcategories.filter(is_active=True).order_by('order')
        data = [{'id': sub.id, 'name': sub.name, 'code': sub.code} for sub in subcategories]
        return JsonResponse({'subcategories': data})
    except LogCategory.DoesNotExist:
        return JsonResponse({'subcategories': []})


def get_table_data(request):
    month = request.GET.get('month')
    if not month:
        month = datetime.today().strftime('%Y-%m')

    users = User.objects.all()
    options = [{"label": user.profile.display_name, "value": user.id} for user in users]

    year, mon = map(int, month.split('-'))
    num_days = monthrange(year, mon)[1]

    records = OperationLog.objects.filter(
        date__year=year, date__month=mon
    )
    record_map = {r.date: r.duty_user_id for r in records}

    data_list = []
    for day in range(1, num_days + 1):
        d = date(year, mon, day)
        user_id = record_map.get(d)
        data_list.append([d.strftime('%Y-%m-%d'), user_id])

    header_list = ["일자", "담당자"]
    data = {
        "headers": header_list,
        "data": data_list,
        'options': options,
    }

    return JsonResponse(data)


@csrf_exempt
def save_table_data(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        rows = payload.get('data', payload)

        for row in rows:
            try:
                date_str, user_id = row[0], row[1]
            except (IndexError, ValueError):
                continue

            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue

            if not user_id:
                continue
            duty_user = get_object_or_404(User, pk=user_id)
            record, created = OperationLog.objects.get_or_create(
                date=dt,
                defaults={'duty_user': duty_user}
            )

            if not created and str(record.duty_user) != str(duty_user):
                record.duty_user = duty_user
                record.save()

        return JsonResponse({'status': 'success'})
