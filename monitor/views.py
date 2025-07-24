from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from monitor.models import OperationLog, OperationLogAttachment
from datetime import date, datetime
from calendar import monthrange
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import User

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
    return render(request, 'operation_log_list.html', {
        'logs': logs,
        'selected_month': month,
    })


@login_required
def operation_log_edit(request, pk):
    log = get_object_or_404(OperationLog, pk=pk)
    if request.method == 'POST':
        form = OperationLogForm(request.POST, request.FILES, instance=log)
        if form.is_valid():
            form.save()
            messages.info(request, '저장되었습니다.')
            return redirect('{}?month={}'.format(
                reverse('operation_log_list'),
                log.date.strftime('%Y-%m')
            ))
    else:
        form = OperationLogForm(instance=log)
    return render(request, 'operation_log_form.html', {'form': form, 'log': log})

def get_workflow_status(check_start, check_complete, completed, approved):
    print(check_start)
    print(check_complete)
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

    return render(request, 'operation_log_detail.html', {
        'log': log,
        'ready': ready,
        'steps': steps,
        'step': current_step+1,
    })


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
        log_type = request.POST.get('log_type')
        content = request.POST.get('monitor_log', '')
        checked = bool(request.POST.get('is_checked'))
        now = timezone.now()

        if log_type == '1':
            log.monitoring_result = content
            log.monitoring_yn = checked
            log.monitoring_user = request.user
            log.monitoring_created_at = now
        elif log_type == '2':
            log.sap_backup_result = content
            log.sap_backup_yn = checked
            log.sap_backup_user = request.user
            log.sap_backup_created_at = now
        elif log_type == '3':
            log.room_backup_result = content
            log.room_backup_yn = checked
            log.room_backup_user = request.user
            log.room_backup_created_at = now
        elif log_type == '4':
            log.cloud_backup_result = content
            log.cloud_backup_yn = checked
            log.cloud_backup_user = request.user
            log.cloud_backup_created_at = now
        elif log_type == '5':
            log.offsite_backup_result = content
            log.offsite_backup_yn = checked
            log.offsite_backup_user = request.user
            log.offsite_backup_created_at = now

        log.save()

        for file_ in request.FILES.getlist('attachments'):
            OperationLogAttachment.objects.create(record=log, file=file_)

    return redirect('operation_log_list')

@login_required
def operation_duty(request):
    month = request.GET.get('month')
    if not month:
        month = datetime.today().strftime('%Y-%m')

    return render(request, 'operation_duty.html', {'selected_month': month})


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