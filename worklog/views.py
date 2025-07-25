import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from .models import Worklog, WorklogFile, WorklogTask
from reports.models import WeeklyReport
from .forms import WorklogForm, WorklogFileForm, WorklogTaskForm
from task.models import Task
import json

class WorklogListView(LoginRequiredMixin, ListView):
    template_name = 'worklog/worklog_list.html'
    context_object_name = 'weeks_data'

    def get_queryset(self):
        # 이 메서드는 직접 사용하지 않고, get_context_data에서 데이터를 생성합니다.
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        weeks_to_display = []
        today = datetime.date.today()

        # 최근 4주, 현재 주, 다음 주 (총 6주)
        for i in range(-4, 2):
            target_date = today + datetime.timedelta(weeks=i)
            year, week_num, _ = target_date.isocalendar()
            weeks_to_display.append((year, week_num))
        
        # 중복 제거 및 정렬
        weeks_to_display = sorted(list(set(weeks_to_display)), reverse=True)

        # 각 주차별로 Worklog 존재 여부 확인
        weeks_data = []
        for year, week_num in weeks_to_display:
            worklog = Worklog.objects.filter(author=user, year=year, week_number=week_num).first()
            temp_worklog = Worklog(year=year, week_number=week_num) # for display
            week_start_date = datetime.date.fromisocalendar(year, week_num, 1)
            week_end_date = week_start_date + datetime.timedelta(days=4)
            weekly_report = WeeklyReport.objects.filter(year=year, week_number=week_num).first()
            editable = True
            if weekly_report:
                editable = weekly_report.editable
     

            weeks_data.append({
                'year': year,
                'week_number': week_num,
                'month_week_display': temp_worklog.month_week_display,
                'worklog_instance': worklog,
                'week_start_date': week_start_date,
                'week_end_date': week_end_date,
                'editable' : editable
            })

        context['weeks_data'] = weeks_data
        context['title'] = "주간업무"
        return context

class WorklogCreateView(LoginRequiredMixin, CreateView):
    model = Worklog
    form_class = WorklogForm
    template_name = 'worklog/worklog_form.html'

    def get(self, request, *args, **kwargs):
        year = self.kwargs.get('year')
        week_number = self.kwargs.get('week_number')
        
        # 해당 주차에 이미 주간업무가 있는지 확인
        if Worklog.objects.filter(author=request.user, year=year, week_number=week_number).exists():
            messages.warning(request, f"{year}년 {week_number}주차의 주간업무는 이미 존재합니다. 수정 화면으로 이동합니다.")
            existing_worklog = Worklog.objects.get(author=request.user, year=year, week_number=week_number)
            return redirect('worklog_update', pk=existing_worklog.pk)
            
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date = datetime.date.fromisocalendar(self.kwargs.get('year'), self.kwargs.get('week_number'), 1)
        end_date = start_date + datetime.timedelta(days=4)
        month_week_display = ''

            # 주의 시작과 끝이 같은 달인 경우
        if start_date.month == end_date.month:
            # 해당 월의 첫 번째 월요일을 찾아서 몇 번째 주인지 계산
            first_monday = start_date.replace(day=1)
            while first_monday.weekday() != 0:  # 0 = 월요일
                first_monday += datetime.timedelta(days=1)
            
            week_diff = (start_date - first_monday).days // 7 + 1
            month_week_display = f"{start_date.month}월 {week_diff}주차"
        else:
            # 주가 두 달에 걸쳐있는 경우, 더 많은 날이 포함된 달 기준
            if start_date.day <= 3:  # 월요일~수요일이 이전 달
                month = end_date.month
                first_monday = end_date.replace(day=1)
                while first_monday.weekday() != 0:
                    first_monday += datetime.timedelta(days=1)
                week_diff = (end_date - first_monday).days // 7 + 1
            else:  # 목요일~일요일이 다음 달
                month = start_date.month
                first_monday = start_date.replace(day=1)
                while first_monday.weekday() != 0:
                    first_monday += datetime.timedelta(days=1)
                week_diff = (start_date - first_monday).days // 7 + 1
            
            month_week_display = f"{month}월 {week_diff}주차"    

        context['title'] = month_week_display
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # 최근 3개의 worklog 추출
        context['recent_worklogs'] = Worklog.objects.filter(author=self.request.user).order_by('-year', '-week_number')[:3]

        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.year = self.kwargs.get('year')
        form.instance.week_number = self.kwargs.get('week_number')
        messages.success(self.request, '주간업무가 성공적으로 생성되었습니다.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('worklog_list')



@login_required
def worklog_add_task(request, worklog_id):
    """주간업무에 Task 추가"""
    print(f"DEBUG: worklog_add_task called with worklog_id={worklog_id}")
    print(f"DEBUG: request.method={request.method}")
    
    try:
        worklog = get_object_or_404(Worklog, id=worklog_id, author=request.user)
        print(f"DEBUG: Found worklog: {worklog}")
        
        if request.method == 'POST':
            form = WorklogTaskForm(request.POST, user=request.user, worklog=worklog)
            print(f"DEBUG: Form created, is_valid={form.is_valid()}")
            
            if form.is_valid():
                worklog_task = form.save(commit=False)
                worklog_task.worklog = worklog
                worklog_task.save()
                messages.success(request, f'업무 "{worklog_task.task.title}"가 주간업무에 추가되었습니다.')
                print(f"DEBUG: Task added successfully: {worklog_task.task.title}")
            else:
                messages.error(request, '업무 추가에 실패했습니다.')
                print(f"DEBUG: Form errors: {form.errors}")
        
        return redirect('worklog_update', pk=worklog.id)
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
        return redirect('worklog_list')

@login_required
def worklog_remove_task(request, worklog_id, task_id):
    """주간업무에서 Task 제거"""
    try:
        worklog = get_object_or_404(Worklog, id=worklog_id, author=request.user)
        worklog_task = get_object_or_404(WorklogTask, worklog=worklog, task_id=task_id)
        
        if request.method == 'POST':
            task_title = worklog_task.task.title
            worklog_task.delete()
            messages.success(request, f'업무 "{task_title}"가 주간업무에서 제거되었습니다.')
        
        return redirect('worklog_update', pk=worklog.id)
        
    except Exception as e:
        messages.error(request, f'업무 제거 중 오류가 발생했습니다: {str(e)}')
        return redirect('worklog_list')

@login_required
def worklog_update_task(request, worklog_id, task_id):
    """주간업무 Task 상태 업데이트"""
    try:
        worklog = get_object_or_404(Worklog, id=worklog_id, author=request.user)
        worklog_task = get_object_or_404(WorklogTask, worklog=worklog, task_id=task_id)
        
        if request.method == 'POST':
            form = WorklogTaskForm(request.POST, instance=worklog_task, user=request.user, worklog=worklog)
            if form.is_valid():
                form.save()
                messages.success(request, '업무 상태가 업데이트되었습니다.')
            else:
                messages.error(request, '업무 상태 업데이트에 실패했습니다.')
        
        return redirect('worklog_update', pk=worklog.id)
        
    except Exception as e:
        messages.error(request, f'업무 상태 업데이트 중 오류가 발생했습니다: {str(e)}')
        return redirect('worklog_list')

@login_required
def get_user_tasks_api(request):
    """사용자의 업무 목록을 JSON으로 반환 (AJAX용)"""
    search = request.GET.get('search', '')
    
    # 사용자가 작성했거나 담당자로 지정된 업무들
    tasks = Task.objects.filter(
        Q(author=request.user) | Q(assigned_to=request.user)
    ).distinct()
    
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    tasks = tasks.order_by('-created_at')[:20]  # 최근 20개만
    
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task.id,
            'title': task.title,
            'status': task.get_status_display(),
            'priority': task.get_priority_display(),
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
            'category': task.category.name if task.category else None,
        })
    
    return JsonResponse({'tasks': task_list})

@login_required
def copy_worklog_api(request, worklog_id):
    """주간업무 내용 복사 API (AJAX용)"""
    try:
        worklog = get_object_or_404(Worklog, id=worklog_id, author=request.user)
        
        return JsonResponse({
            'success': True,
            'this_week_work': worklog.this_week_work or '',
            'next_week_plan': worklog.next_week_plan or '',
            'worklog_info': {
                'week_display': worklog.month_week_display,
                'created_at': worklog.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


class WorklogUpdateView(LoginRequiredMixin, UpdateView):
    model = Worklog
    form_class = WorklogForm
    template_name = 'worklog/worklog_form.html'
    success_url = reverse_lazy('worklog_list')

    def get_queryset(self):
        return Worklog.objects.filter(author=self.request.user)

    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 현재 주차 정보
        current_year, current_week = Worklog.get_current_week_info()
        context['current_year'] = current_year
        context['current_week'] = current_week
        
        # 현재 주차의 월별 표시를 위한 임시 주간업무 객체 생성
        temp_worklog = Worklog(year=current_year, week_number=current_week)
        context['current_month_week'] = temp_worklog.month_week_display
        
        # 사용자의 최근 주간업무 목록 (현재 수정중인 것 제외, 최근 5개)
        context['recent_worklogs'] = Worklog.objects.filter(
            author=self.request.user
        ).exclude(pk=self.object.pk).order_by('-year', '-week_number')[:5]
        
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '주간업무가 성공적으로 수정되었습니다.')
        return response

class WorklogDeleteView(LoginRequiredMixin, DeleteView):
    model = Worklog
    template_name = 'worklog/worklog_confirm_delete.html'
    success_url = reverse_lazy('worklog_list')

    def get_queryset(self):
        return Worklog.objects.filter(author=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, '주간업무가 성공적으로 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)

class WorklogDetailView(LoginRequiredMixin, DetailView):
    model = Worklog
    template_name = 'worklog/worklog_detail.html'
    context_object_name = 'worklog'

    def get_queryset(self):
        return Worklog.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        weekly_report = WeeklyReport.objects.filter(year=self.object.year, week_number=self.object.week_number).first()
        print(weekly_report)
        context['editable'] = weekly_report.editable if weekly_report else True
        context['file_form'] = WorklogFileForm()
        context['files'] = self.object.files.all()
        return context


@login_required
def upload_worklog_file(request, worklog_id):
    """주간업무에 파일 업로드"""
    worklog = get_object_or_404(Worklog, id=worklog_id, author=request.user)
    
    if request.method == 'POST':
        form = WorklogFileForm(request.POST, request.FILES)
        if form.is_valid():
            worklog_file = form.save(commit=False)
            worklog_file.worklog = worklog
            worklog_file.uploaded_by = request.user
            worklog_file.original_name = request.FILES['file'].name
            worklog_file.save()
            
            messages.success(request, '파일이 업로드되었습니다.')
        else:
            messages.error(request, '파일 업로드에 실패했습니다.')
    
    return redirect('worklog_detail', pk=worklog_id)

@login_required
def download_worklog_file(request, file_id):
    """주간업무 파일 다운로드"""
    worklog_file = get_object_or_404(WorklogFile, id=file_id, worklog__author=request.user)
    
    try:
        response = HttpResponse(worklog_file.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{worklog_file.original_name}"'
        return response
    except Exception as e:
        messages.error(request, '파일 다운로드 중 오류가 발생했습니다.')
        return redirect('worklog_detail', pk=worklog_file.worklog.id)


