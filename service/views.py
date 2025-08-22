import datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    ServiceRequest,
    ServiceRequestAttachment,
    ServiceInspection,
    ServiceRelease,
    User,
    CommonCode,
    ServiceRequestStep,
)
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime, date, timedelta
from django.db.models import Q, Count, Sum, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.core.mail import EmailMessage


@login_required
def send_simple_mail(title, body, receiver):
    mode = 'TEST'

    mail_template = '<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">  <title>삼천리 IT 관리시스템</title>'
    mail_template +='<style type="text/css">  body { margin-left: 0px; margin-top: 0px; margin-right: 0px; margin-bottom: 0px; } </style> </head>'
    mail_template +='<body><div style="position:absolute; width:100%;  overflow:hidden; border-top:#d64b72 solid 2px; font-family:맑은 고딕;color:#6d6d6d;line-height:30px;overflow:hidden; border-top:#d64b72 solid; border-bottom:#d64b72 solid 2px;font-family:Dotum,돋움,sans-serif;color:#6d6d6d;line-height:30px;  no-repeat;font-size:13px;">'
    mail_template += '<center> <table width="100%" border="0" cellspacing="0" cellpadding="20"><tr><td><b>삼천리 IT 관리시스템</b></td></tr><tr><td>'
    mail_template += body
    mail_template +='</td></tr> <tr><td>삼천리 IT 관리시스템 <a href="https://secure.serveone.co.kr">바로가기</a> &nbsp URL : https://secure.serveone.co.kr'
    mail_template +='<br>* 본 메일은 발신전용 메일입니다. 문의나 연락은 IT서비스2팀 담당자에게 해주시기 바랍니다. *</p></td></tr></table> </div></body>'

    #테스트용 메일수신자
    if mode == 'TEST':
        print('mail to : ')
        print(receiver)
        receiver = ['ziid@samchully.co.kr']

    email = EmailMessage(
        title,  # 제목
        mail_template,  # 내용
        'ziid@samchully.co.kr', # 발신자
        to=receiver,  # 받는 이메일 리스트
    )
    email.content_subtype = "html"
    rtn = email.send()

    return rtn

@login_required
def service_request_type_list(request):
    service_list = CommonCode.objects.filter(group='service').filter(active=True).order_by('code')

    data = {
        'service_list': service_list

    }

    return render(request, 'service_request.html', data)


def create_step(service_request, user, msg, status):
        service_step = ServiceRequestStep(
            service_request=service_request,
            user=user,
            content=msg,
            status=status,
        )
        return service_step.save()

@login_required
def service_request_create(request, code):
    url = reverse('service_request_create', kwargs={'code': code})
    
    if request.method == 'POST':

        try:
            req_type = CommonCode.objects.get(group='service', code=code)
        except CommonCode.DoesNotExist:
            messages.error(request, "잘못된 요청 유형입니다.")
            return redirect(url)

        service_request = ServiceRequest.objects.create(
            req_user=request.user,
            req_type=req_type,
            req_title=request.POST.get('req_title'),
            req_system=request.POST.get('req_system'),
            req_module=request.POST.get('req_module'),
            req_depart=request.POST.get('req_depart'),
            req_name=request.POST.get('req_name'),
            req_email=request.POST.get('req_email'),
            req_reason=request.POST.get('req_reason'),
            req_details=request.POST.get('req_details'),
            rcv_opinion=request.POST.get('rcv_opinion'),
            date_of_req=request.POST.get('date_of_req') and datetime.strptime(request.POST.get('date_of_req'), '%Y-%m-%d').date() or None,
            date_of_due=request.POST.get('date_of_due') and datetime.strptime(request.POST.get('date_of_due'), '%Y-%m-%d').date() or None,
            assignee=request.user,
            effort_expected=request.POST.get('effort_expected'),            
        )

        # Handle file uploads
        for file_ in request.FILES.getlist('attachments'):
            ServiceRequestAttachment.objects.create(record=service_request, file=file_)
        create_step(service_request, request.user, '서비스 요청 생성', 'N')
        messages.success(request, "서비스 요청이 성공적으로 생성되었습니다.")
        return redirect('service_request_list') # Redirect to a list view

    #types = UserRequestTypeMaster.objects.all()
    try:
        selected_type = CommonCode.objects.get(group='service', code=code) 
    except CommonCode.DoesNotExist:
        messages.error(request, "잘못된 요청 유형입니다.")
        return redirect(url) 
    
    assignees = User.objects.all()
    systems = CommonCode.objects.filter(group='system').filter(active=True)
    modules = CommonCode.objects.filter(group='module').filter(active=True)
    context = {
        'selected_type' : selected_type,
        'type': code, 
        'assignees': assignees,
        'systems': systems,
        'modules': modules,
        }
    return render(request, 'service_request_form.html', context)

@login_required
def service_request_list(request):
    service_requests = ServiceRequest.objects.filter(Q(status__in=["N", "P"]), assignee=request.user).order_by('-id')
    return render(request, 'service_request_list.html', {'service_requests': service_requests, 'today': date.today()})

def service_request_list_search(request):
    managers = User.objects.all()
    services = CommonCode.objects.filter(group='service', active=True)
    systems = CommonCode.objects.filter(group='system', active=True)
    modules = CommonCode.objects.filter(group='module', active=True)

    # GET 파라미터 받기
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    req_system = request.GET.get('req_system')
    req_module = request.GET.get('req_module')
    req_manager = request.GET.get('req_manager')
    if not req_manager:
        req_manager = request.user.id

    req_type = request.GET.get('req_type')

    selected_manager = User.objects.filter(id=req_manager).first()
    statuses = CommonCode.objects.filter(group='status', active=True)
    selected_type = CommonCode.objects.filter(group='service', code=req_type, active=True).first()
    selected_statuses = request.GET.getlist('status')  # 여러 개 선택 가능

    # 시작일/종료일 필수 체크
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            service_requests = ServiceRequest.objects.filter(created_at__date__range=(start_date, end_date)).order_by('-id')
        except ValueError:
            # 날짜 파싱 실패 시 예외 처리 (옵션)
            service_requests = ServiceRequest.objects.all().order_by('-id')
    else:
        # 최초 조회는 오늘부터 1개월 전까지   
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        service_requests = ServiceRequest.objects.filter(created_at__date__range=(start_date, end_date)).order_by('-id')

    # 선택 필터 적용
    if req_system:
        service_requests = service_requests.filter(req_system=req_system)

    if req_module:
        service_requests = service_requests.filter(req_module=req_module)

    if req_manager:
        service_requests = service_requests.filter(assignee=req_manager)
    
    if selected_statuses:
        service_requests = service_requests.filter(status__in=selected_statuses)
    
    if selected_type:
        service_requests = service_requests.filter(req_type=selected_type)
        print(selected_type)

    context = {
        'service_requests': service_requests,
        'managers': managers,
        'today': date.today(),
        'services': services,
        'systems': systems,
        'modules': modules,
        'statuses': statuses,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_system': req_system,
        'selected_module':req_module,
        'selected_manager':selected_manager,
        'selected_statuses': selected_statuses,
        'selected_type': selected_type,
 
    }

    return render(request, 'service_request_list_search.html', context)

@login_required
def service_request_detail(request, pk):
    # 특정 요청의 상세 정보를 가져옵니다.
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    assignees = User.objects.all()
    systems = CommonCode.objects.filter(group='system').filter(active=True)
    modules = CommonCode.objects.filter(group='module').filter(active=True)

    if service_request.parent_sr is not None:
        attatchments_sr = service_request.get_root_sr()
    else:
        attatchments_sr = service_request

    context ={
        'service_request': service_request,
        "assignees": assignees,
        'attatchments_sr': attatchments_sr,
        'systems': systems,
        'modules': modules,
        'inspections': ServiceInspection.objects.filter(service_request=service_request).order_by('seq'),
        'releases': ServiceRelease.objects.filter(service_request=service_request).order_by('created_at'),
    }
    return render(request, 'service_request_detail.html', context)

def service_request_approve(request, pk):
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        service_request.status = 'P'  # 상태를 '진행중'으로 변경
        service_request.save()
        create_step(service_request, request.user, '요청 승인', 'N')

        return redirect('service_request_detail', pk=pk)


def service_request_inspection_result(request, token):
    inspection = get_object_or_404(ServiceInspection, token=token)
    if request.method == 'POST':
        inspection.test_result = request.POST.get('test_result')
        inspection.result = request.POST.get('result')
        inspection.result_at = timezone.now()
        inspection.save()
        msg = '검수 완료' if inspection.result == 'C' else '재작업 요청'
        create_step(inspection.service_request, None, msg, 'P')
        return render(request, 'inspection_result_done.html')
    return render(request, 'inspection_result_form.html', {'inspection': inspection})

def service_request_assign(request, pk):
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        assignee = get_object_or_404(User, pk=request.POST.get('assignee'))
        new_assignee = get_object_or_404(User, pk=request.POST.get('new_assignee'))
        msg = "담당자 변경 (기존 : " + assignee.profile.display_name + ", 신규 : "+ new_assignee.profile.display_name + ")"
        
        if assignee:
            service_request.assignee = new_assignee  # 담당자 필드 업데이트
            service_request.status='P'
            service_request.save()
            create_step(service_request, request.user, msg, 'P')
        
        return redirect('service_request_detail', pk=pk)
    
def child_service_request_create(request, pk):
    parent_sr = ServiceRequest.objects.get(pk=pk)
    new_assignee = get_object_or_404(User, pk=request.POST.get('split_assignee'))
    split_content = request.POST.get('split_content')
    new_date_of_due = request.POST.get('new_date_of_due')
    split_req_system = request.POST.get('split_req_system')
    split_req_module = request.POST.get('split_req_module')

    if request.method == 'POST':

        service_request = ServiceRequest.objects.create(
            parent_sr=parent_sr,
            req_user=parent_sr.req_user,
            req_type=parent_sr.req_type,
            req_title=parent_sr.req_title,
            req_system=split_req_system,
            req_module=split_req_module,
            req_depart=parent_sr.req_depart,
            req_name=parent_sr.req_name,
            req_email=parent_sr.req_email,
            req_reason=parent_sr.req_reason,
            req_details=parent_sr.req_details,
            split_msg=split_content,
            date_of_req=parent_sr.date_of_req,
            split_date_of_due=new_date_of_due,
            assignee=new_assignee,
            
         
        )
        create_step(service_request, request.user, 'SR No. '+str(parent_sr.id) + '에서 분할 생성', 'N')
        create_step(parent_sr, request.user, 'SR No. '+str(service_request.id) + '로 분할', 'P')

    return redirect('service_request_detail', pk=pk)

def service_request_accept(request, pk):
    
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        service_request.status = 'P'  # 상태를 '진행중'으로 변경   
        service_request.date_of_due = request.POST.get('accept_date_of_due')
        service_request.rcv_opinion = request.POST.get('accept_content')
        service_request.effort_expected= request.POST.get('accept_effort_expected')
        service_request.save()
        create_step(service_request, request.user, '분할 SR 요청 접수', 'N')
            
        return redirect('service_request_detail', pk=pk)

def service_request_inspection(request, pk):
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        seq = ServiceInspection.objects.filter(service_request=service_request).count() + 1
        inspection = ServiceInspection.objects.create(
            service_request=service_request,
            seq=seq,
            inspector_name=request.POST.get('inspector_name'),
            inspector_email=request.POST.get('inspector_email'),
            dev_test_detail=request.POST.get('dev_test_detail'),
            test_request=request.POST.get('test_request'),
        )
        link = request.build_absolute_uri(reverse('service_request_inspection_result', args=[inspection.token]))
        mail_body = '<br>SR 테스트 요청이 있습니다.<br>'
        mail_body += f'<a href="{link}">검수 결과 입력</a>'
        print(link)
        #send_simple_mail('[ITMS] 테스트 요청', mail_body, [inspection.inspector_email])
        create_step(service_request, request.user, '검수 요청 '+link, 'P')
        return redirect('service_request_detail', pk=pk)

def service_request_release(request, pk):
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        release = ServiceRelease.objects.create(
            service_request=service_request,
            release_date=request.POST.get('release_date'),
            source_system=request.POST.get('source_system'),
            target_system=request.POST.get('target_system'),
            request_number=request.POST.get('request_number'),
            description=request.POST.get('description'),
        )
        create_step(service_request, request.user, 'CTS/릴리즈 요청', 'P')
    return redirect('service_request_detail', pk=pk)

def service_request_release_approve(request, pk):
    release = get_object_or_404(ServiceRelease, pk=pk)
    release.approved = True
    release.approved_by = request.user
    release.approved_at = timezone.now()
    release.save()
    create_step(release.service_request, request.user, 'CTS/릴리즈 승인', 'P')
    return redirect('service_admin_release_list')


@login_required
def service_admin_approve_list(request):
    pending_requests = ServiceRequest.objects.filter(status='N', parent_sr__isnull=True)
    pending_releases = ServiceRelease.objects.filter(approved=False)

    pending_items = []

    for sr in pending_requests:
        pending_items.append({
            'type': 'sr',
            'created_at': sr.created_at,
            'sr': sr,
        })

    for rl in pending_releases:
        pending_items.append({
            'type': 'release',
            'created_at': rl.created_at,
            'release': rl,
        })

    pending_items.sort(key=lambda x: x['created_at'], reverse=True)

    context = {
        'pending_items': pending_items,
    }
    return render(request, 'ServiceAdminApprove_list.html', context)


@login_required
def service_admin_request_list(request):
    """신규 SR 승인 대기 목록"""
    pending_requests = ServiceRequest.objects.filter(status='N', parent_sr__isnull=True).order_by('-created_at')
    return render(request, 'ServiceAdminRequest_list.html', {'pending_requests': pending_requests})


@login_required
def service_admin_release_list(request):
    """CTS/릴리즈 승인 대기 목록"""
    pending_releases = ServiceRelease.objects.filter(approved=False).order_by('-created_at')
    return render(request, 'ServiceAdminRelease_list.html', {'pending_releases': pending_releases})


def service_request_complete(request, pk):
    
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        service_request.status = 'G'  # 상태를 '완료'로 변경   
        service_request.date_of_complete = request.POST.get('date_of_complete')
        service_request.complete_content = request.POST.get('complete_content')
        service_request.effort= request.POST.get('complete_effort')
        service_request.save()
        create_step(service_request, request.user, '처리 완료', 'P')
            
        return redirect('service_request_detail', pk=pk)


@login_required
def service_request_report(request):
    """월별 담당자별 SR 처리 현황 리포트"""

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today() - timedelta(days=180)
            end_date = date.today()
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=180)

    srs = ServiceRequest.objects.filter(created_at__date__range=(start_date, end_date))

    monthly_assignee = srs.annotate(month=TruncMonth('created_at')).values('month', 'assignee__username')\
        .annotate(total=Count('id'),
                 effort=Sum('effort'),
                 delayed=Count('id', filter=Q(date_of_complete__gt=F('date_of_due'))))\
        .order_by('month', 'assignee__username')

    months = sorted({m['month'].strftime('%Y-%m') for m in monthly_assignee})
    assignees = sorted({m['assignee__username'] or '미정' for m in monthly_assignee})

    count_data = {a: {m: 0 for m in months} for a in assignees}
    effort_data = {a: {m: 0 for m in months} for a in assignees}
    delay_data = {a: {m: 0 for m in months} for a in assignees}

    for row in monthly_assignee:
        month = row['month'].strftime('%Y-%m')
        assignee = row['assignee__username'] or '미정'
        count_data[assignee][month] = row['total']
        effort_data[assignee][month] = float(row['effort'] or 0)
        delay_data[assignee][month] = row['delayed']

    system_counts = list(srs.values('req_system').annotate(count=Count('id')).order_by('req_system'))

    context = {
        'months': months,
        'assignees': assignees,
        'count_data': count_data,
        'effort_data': effort_data,
        'delay_data': delay_data,
        'system_counts': system_counts,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }

    return render(request, 'service_request_report.html', context)
