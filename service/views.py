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
    ServiceRequestFormData,
    FormElement,
    Dataset,
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
from teams.models import Team


@login_required
def service_request_type_list(request):
    service_list = CommonCode.objects.filter(group='service').filter(active=True).order_by('code')

    data = {
        'service_list': service_list

    }

    return render(request, 'service/service_request.html', data)


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
    print('service_request_create')
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
        
        # Handle dynamic form data
        if req_type.dataset:
            form_html = []
            for key, value in request.POST.items():
                if key not in ['csrfmiddlewaretoken', 'req_title', 'req_system', 'req_module', 'req_manager',
                              'req_depart', 'req_name', 'req_email', 'req_reason', 'req_details', 
                              'rcv_opinion', 'date_of_req', 'date_of_due', 'effort_expected','attachments','status']:
                    dataset_filter = Dataset.objects.get(code=req_type.dataset)
                    print(dataset_filter.code)
                    print(key)
                    
                    element = get_object_or_404(FormElement, dataset=dataset_filter, element_code=key)   

                    print(element)
                    ServiceRequestFormData.objects.create(
                        service_request=service_request,
                        dataset=req_type.dataset,
                        field_key=element.element_name,
                        field_value=value
                    )
                    # Add to HTML generation
                    form_html.append(f'<div class="mb-2"><strong>{element.element_name}:</strong> {value}</div>')
            
            # Update req_details with generated HTML
            if form_html:
                service_request.req_details = ''.join(form_html)
                service_request.save()
        messages.success(request, "서비스 요청이 성공적으로 생성되었습니다.")
        return redirect('service_request_list') # Redirect to a list view

    #types = UserRequestTypeMaster.objects.all()
    try:
        selected_type = CommonCode.objects.get(group='service', code=code) 
    except CommonCode.DoesNotExist:
        messages.error(request, "잘못된 요청 유형입니다.")
        return redirect(url) 
    
    assignees = User.objects.exclude(id=request.user.id)
    systems = CommonCode.objects.filter(group='system').filter(active=True)
    modules = CommonCode.objects.filter(group='module').filter(active=True)
    
    # Load form elements for dataset
    form_elements = []
    dataset_name = ""
    if selected_type.dataset:
        try:
            dataset = Dataset.objects.get(code=selected_type.dataset)
            form_elements = dataset.elements.filter(active=True).order_by('order')
            dataset_name = dataset.name
            
            # Parse JSON options for select/radio elements
            for element in form_elements:
                if element.element_options:
                    try:
                        import json
                        element.options = json.loads(element.element_options)
                    except:
                        element.options = []
                else:
                    element.options = []
        except Dataset.DoesNotExist:
            pass
    
    context = {
        'selected_type' : selected_type,
        'type': code, 
        'assignees': assignees,
        'systems': systems,
        'modules': modules,
        'form_elements': form_elements,
        'dataset_code': selected_type.dataset,
        'dataset_name': dataset_name,        
        }
    
    return render(request, 'service/service_request_form.html', context)

@login_required
def service_request_reception_create(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)

    if request.method == 'POST':


        service_request.rcv_opinion = request.POST.get('rcv_opinion')
        service_request.date_of_due = request.POST.get('date_of_due') or None
        service_request.effort_expected = request.POST.get('effort_expected')
        service_request.status = 'A'
        service_request.save()

        # Handle file uploads
        for file_ in request.FILES.getlist('attachments'):
            ServiceRequestAttachment.objects.create(record=service_request, file=file_, file_type='RCV')
        create_step(service_request, request.user, '서비스 접수완료', 'A')
        
        messages.success(request, "서비스 접수가 완료되었습니다.")
        return redirect('service_request_reception_list') # Redirect to a list view

    assignees = User.objects.all()
    systems = CommonCode.objects.filter(group='system').filter(active=True)
    modules = CommonCode.objects.filter(group='module').filter(active=True)

    if service_request.parent_sr is not None:
        attatchments_sr = service_request.get_root_sr()
    else:
        attatchments_sr = service_request


    try:
        selected_type = CommonCode.objects.get(group='service', code='9001') 
    except CommonCode.DoesNotExist:
        messages.error(request, "잘못된 요청 유형입니다.")
        return redirect(url) 
    
    assignees = User.objects.all()
    systems = CommonCode.objects.filter(group='system').filter(active=True)
    modules = CommonCode.objects.filter(group='module').filter(active=True)
    
    # Load form elements for dataset
    form_elements = []
    dataset_name = ""
    if selected_type.dataset:
        try:
            dataset = Dataset.objects.get(code=selected_type.dataset)
            form_elements = dataset.elements.filter(active=True).order_by('order')
            dataset_name = dataset.name
            
            # Parse JSON options for select/radio elements
            for element in form_elements:
                if element.element_options:
                    try:
                        import json
                        element.options = json.loads(element.element_options)
                    except:
                        element.options = []
                else:
                    element.options = []
        except Dataset.DoesNotExist:
            pass
    
    context = {
        'selected_type' : selected_type,
        'assignees': assignees,
        'systems': systems,
        'modules': modules,
        'form_elements': form_elements,
        'dataset_code': selected_type.dataset,
        'dataset_name': dataset_name,     
        'service_request': service_request,
        "assignees": assignees,
        'attatchments_sr': attatchments_sr,
        'systems': systems,
        'modules': modules,
        'inspections': ServiceInspection.objects.filter(service_request=service_request).order_by('seq'),
        'releases': ServiceRelease.objects.filter(service_request=service_request).order_by('created_at'),   
        'sr_teams': Team.objects.filter(is_sr_team=True).prefetch_related('members__profile'),
        }
    
    return render(request, 'service/service_request_reception_form.html', context)


@login_required
def service_request_list(request):
    service_requests = ServiceRequest.objects.filter(Q(status__in=["A", "P"]), assignee=request.user).order_by('id')
    return render(request, 'service/service_request_list.html', {'service_requests': service_requests, 'today': date.today()})

@login_required
def service_request_reception_list(request):
    """SR 접수 - 상태가 'N'이고 담당자가 본인인 SR 목록"""
    reception_requests = ServiceRequest.objects.filter(status='N', assignee=request.user).order_by('created_at')
    context = {
        'service_requests': reception_requests,
        'today': date.today()
    }
    return render(request, 'service/service_request_reception_list.html', context)


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
    if req_manager is None:
        req_manager = request.user.id
    elif req_manager == "":
        req_manager = None

    req_type = request.GET.get('req_type')

    if req_manager:
        selected_manager = User.objects.filter(id=req_manager).first()
    else:
        selected_manager = None
    # statuses = CommonCode.objects.filter(group='status', active=True)
    statuses = [
        {"code": "N", "name": "서비스 생성"},
        {"code": "A", "name": "승인 대기"},
        {"code": "P", "name": "처리중"},
        {"code": "G", "name": "처리완료"},
        {"code": "D", "name": "처리불가"}
    ]
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

    return render(request, 'service/service_request_list_search.html', context)

@login_required
def service_request_detail(request, pk):
    # 특정 요청의 상세 정보를 가져옵니다.
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    assignees = User.objects.exclude(id=request.user.id)
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
        'sr_teams': Team.objects.filter(is_sr_team=True).prefetch_related('members__profile'),
    }
    return render(request, 'service/service_request_detail.html', context)

def service_request_approve(request, pk):
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        service_request.status = 'P'  # 상태를 '진행중'으로 변경
        service_request.save()
        create_step(service_request, request.user, '요청 승인', 'A')
        messages.success(request, '요청이 승인되었습니다.')
        return redirect('service_admin_approve_list')


def service_request_inspection_result(request, token):
    inspection = get_object_or_404(ServiceInspection, token=token)
    if request.method == 'POST':
        inspection.test_result = request.POST.get('test_result')
        inspection.result = request.POST.get('result')
        inspection.result_at = timezone.now()
        inspection.save()
        msg = '검수 완료' if inspection.result == 'C' else '재작업 요청'
        create_step(inspection.service_request, None, msg, 'P')
        return render(request, 'service/inspection_result_done.html')
    return render(request, 'service/inspection_result_form.html', {'inspection': inspection})

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

@login_required
def service_request_step_create(request, pk):
    """SR 진행 상황(Step) 추가"""
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        content = request.POST.get('step_content')
        
        # Create Step
        step = ServiceRequestStep.objects.create(
            service_request=service_request,
            user=request.user,
            content=content,
            status='P'  # 기본적으로 진행중(P) 상태로 기록
        )
        
        # Handle Attachments
        if request.FILES.getlist('attachments'):
            for file_ in request.FILES.getlist('attachments'):
                ServiceRequestAttachment.objects.create(
                    record=service_request, 
                    step=step,
                    file=file_,
                    file_type='STEP'
                )
        
        messages.success(request, '진행 상황이 등록되었습니다.')
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
    messages.success(request, 'CTS/릴리즈가 승인되었습니다.')
    return redirect('service_admin_approve_list')


@login_required
def service_admin_approve_list(request):
    pending_requests = ServiceRequest.objects.filter(status='A', parent_sr__isnull=True)
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
    return render(request, 'service/ServiceAdminApprove_list.html', context)




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

    return render(request, 'service/service_request_report.html', context)


@login_required
def dataset_data_list(request, dataset):
    """특정 dataset을 가진 서비스 요청 목록과 폼 데이터"""
    service_requests = ServiceRequest.objects.filter(
        req_type__dataset=dataset
    ).prefetch_related('form_data').order_by('-created_at')
    
    # 해당 dataset의 모든 필드명 수집
    field_keys = ServiceRequestFormData.objects.filter(
        dataset=dataset
    ).values_list('field_key', flat=True).distinct()
    
    context = {
        'dataset': dataset,
        'service_requests': service_requests,
        'field_keys': field_keys,
    }
    
    return render(request, 'service/dataset_data_list.html', context)


@login_required
def dataset_status_list(request):
    """데이터셋별 요청 현황 조회"""
    datasets = CommonCode.objects.filter(
        group='service', 
        dataset__isnull=False
    ).exclude(dataset='').values('dataset', 'name').distinct()
    
    dataset_stats = []
    for dataset_info in datasets:
        dataset = dataset_info['dataset']
        service_name = dataset_info['name']
        
        total_count = ServiceRequest.objects.filter(req_type__dataset=dataset).count()
        status_counts = ServiceRequest.objects.filter(req_type__dataset=dataset).values('status').annotate(count=Count('id'))
        
        stats = {
            'dataset': dataset,
            'service_name': service_name,
            'total': total_count,
            'status_counts': {item['status']: item['count'] for item in status_counts}
        }
        dataset_stats.append(stats)
    
    context = {
        'dataset_stats': dataset_stats,
    }
    
    return render(request, 'service/dataset_status_list.html', context)


@login_required
def form_element_list(request):
    """데이터셋 목록 (요소 개수 포함)"""
    from django.db.models import Count
    datasets = Dataset.objects.annotate(
        element_count=Count('elements')
    ).order_by('code')
    
    context = {
        'datasets': datasets,
    }
    return render(request, 'service/form_element_list.html', context)


@login_required
def form_element_create(request):
    """폼 요소 생성"""
    if request.method == 'POST':
        dataset_name = request.POST['dataset_name']
        dataset_code = request.POST['dataset_code']
        
        # Get or create dataset
        dataset, created = Dataset.objects.get_or_create(
            code=dataset_code,
            defaults={'name': dataset_name}
        )
        
        # Process multiple elements
        elements_data = {}
        for key, value in request.POST.items():
            if key.startswith('elements[') and '][' in key:
                import re
                match = re.match(r'elements\[(\d+)\]\[([^\]]+)\]', key)
                if match:
                    index = int(match.group(1))
                    field = match.group(2)
                    
                    if index not in elements_data:
                        elements_data[index] = {}
                    elements_data[index][field] = value
        
        # Create FormElement objects
        for index, element_data in elements_data.items():
            is_required_key = f"elements[{index}][is_required]"
            FormElement.objects.create(
                dataset=dataset,
                element_name=element_data['element_name'],
                element_code=element_data['element_code'],
                element_type=element_data['element_type'],
                is_required=is_required_key in request.POST,
                placeholder=element_data.get('placeholder', ''),
                order=int(element_data.get('order', 0)),
            )
        
        return redirect('form_element_list')
    
    return render(request, 'service/form_element_form.html', {'action': 'create'})


@login_required
def form_element_edit(request, pk):
    """폼 요소 수정"""
    element = get_object_or_404(FormElement, pk=pk)
    
    if request.method == 'POST':
        dataset_name = request.POST['dataset_name']
        dataset_code = request.POST['dataset_code']
        
        # Update dataset
        element.dataset.name = dataset_name
        element.dataset.code = dataset_code
        element.dataset.save()
        
        # Handle both old format (direct fields) and new format (array)
        if 'elements[0][element_name]' in request.POST:
            # New array format
            element.element_name = request.POST['elements[0][element_name]']
            element.element_code = request.POST['elements[0][element_code]']
            element.element_type = request.POST['elements[0][element_type]']
            element.is_required = 'elements[0][is_required]' in request.POST
            element.placeholder = request.POST.get('elements[0][placeholder]', '')
            element.order = int(request.POST.get('elements[0][order]', 0))
        
        element.save()
        return redirect('form_element_list')
    
    context = {'element': element, 'action': 'edit'}
    return render(request, 'service/form_element_form.html', context)


@login_required
def form_element_delete(request, pk):
    """폼 요소 삭제"""
    element = get_object_or_404(FormElement, pk=pk)
    element.delete()
    return redirect('form_element_list')


@login_required
def dataset_detail(request, pk):
    """데이터셋 상세 - 요소 관리"""
    dataset = get_object_or_404(Dataset, pk=pk)
    elements = dataset.elements.all().order_by('order')
    
    if request.method == 'POST':
        # Update dataset info
        dataset.name = request.POST['dataset_name']
        dataset.code = request.POST['dataset_code']
        dataset.description = request.POST.get('dataset_description', '')
        dataset.save()
        
        # Process elements
        elements_data = {}
        for key, value in request.POST.items():
            if key.startswith('elements[') and '][' in key:
                import re
                match = re.match(r'elements\[(\d+)\]\[([^\]]+)\]', key)
                if match:
                    index = int(match.group(1))
                    field = match.group(2)
                    
                    if index not in elements_data:
                        elements_data[index] = {}
                    elements_data[index][field] = value
        
        # Delete existing elements and create new ones
        dataset.elements.all().delete()
        
        for index, element_data in elements_data.items():
            if element_data.get('element_name') and element_data.get('element_code'):
                is_required_key = f"elements[{index}][is_required]"
                FormElement.objects.create(
                    dataset=dataset,
                    element_name=element_data['element_name'],
                    element_code=element_data['element_code'],
                    element_type=element_data['element_type'],
                    is_required=is_required_key in request.POST,
                    placeholder=element_data.get('placeholder', ''),
                    order=int(element_data.get('order', index)),
                    row_group=element_data.get('row_group', ''),
                    col_width=int(element_data.get('col_width', 12)),
                )
        
        return redirect('dataset_detail', pk=pk)
    
    context = {
        'dataset': dataset,
        'elements': elements,
        'action': 'edit'
    }
    return render(request, 'service/dataset_detail.html', context)


@login_required
def dataset_delete(request, pk):
    """데이터셋 삭제"""
    dataset = get_object_or_404(Dataset, pk=pk)
    dataset.delete()
    return redirect('form_element_list')
