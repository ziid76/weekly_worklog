from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Task, Category, TaskComment, TaskFile
from .forms import TaskForm, CategoryForm, TaskCommentForm, TaskFileForm, TaskSearchForm
from notifications.utils import (
    notify_comment_added,
    notify_task_assigned,
    notify_task_assignment_changes,
    notify_task_status_changed,
)
from django.template.loader import render_to_string


@login_required
def get_user_tasks_api(request):
    if request.method != "GET":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    search = request.GET.get("search", "").strip()
    queryset = Task.objects.filter(
        Q(author=request.user) | Q(assigned_to=request.user)
    ).distinct().select_related("category")

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    tasks = []
    for task in queryset.order_by("-updated_at")[:50]:
        tasks.append(
            {
                "id": task.id,
                "title": task.title,
                "priority": task.get_priority_display(),
                "status": task.get_status_display(),
                "category": task.category.name if task.category else None,
                "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
            }
        )

    return JsonResponse({"tasks": tasks}, json_dumps_params={"ensure_ascii": False})

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'task/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        # 작성자이거나 담당자로 지정된 업무들을 모두 조회
        queryset = Task.objects.filter(
            Q(author=self.request.user) | Q(assigned_to=self.request.user)
        ).distinct().select_related('author', 'category', 'team').prefetch_related('assigned_to')
        
        # 검색 필터링
        self.query_params = self.request.GET.copy()
        
        if 'query' in self.query_params and self.query_params['query']:
             queryset = queryset.filter(
                Q(title__icontains=self.query_params['query']) | Q(description__icontains=self.query_params['query'])
            )
        
        if 'priority' in self.query_params and self.query_params['priority']:
            queryset = queryset.filter(priority=self.query_params['priority'])
            
        if 'category' in self.query_params and self.query_params['category']:
            queryset = queryset.filter(category_id=self.query_params['category'])
            
        # 상태 카운트를 위한 쿼리셋 저장
        self.base_queryset = queryset
        
        if 'status' in self.query_params and self.query_params['status']:
            queryset = queryset.filter(status=self.query_params['status'])
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaskSearchForm(self.request.GET)
        context['categories'] = Category.objects.all()
        
        # 상태별 카운트 (상태 필터 제외한 나머지 필터 적용 기준)
        counts_data = self.base_queryset.values('status').annotate(count=Count('id', distinct=True))
        status_counts = {choice[0]: 0 for choice in Task.STATUS_CHOICES}
        total_sum = 0
        for item in counts_data:
            s_type = item['status']
            s_count = item['count']
            if s_type in status_counts:
                status_counts[s_type] += s_count
            total_sum += s_count
        status_counts['total'] = total_sum
        context['status_counts'] = status_counts
        
        return context

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'task/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        # 작성자이거나 담당자로 지정된 업무들을 모두 조회
        return Task.objects.filter(
            Q(author=self.request.user) | Q(assigned_to=self.request.user)
        ).distinct().select_related('author', 'category', 'team').prefetch_related('assigned_to', 'comments', 'files')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        context['comments'] = task.comments.select_related('author').all()
        context['files'] = task.files.select_related('uploaded_by').all()
        context['is_author'] = task.author == self.request.user
        context['is_assigned'] = self.request.user in task.assigned_to.all()
        context['comment_form'] = TaskCommentForm()
        context['file_form'] = TaskFileForm()
        return context

class TaskBoardView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'task/task.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(
            Q(author=self.request.user) | Q(assigned_to=self.request.user)
        ).distinct().select_related('author', 'category', 'team').prefetch_related('assigned_to', 'comments', 'files').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = context['tasks']
        if tasks.exists():
            selected_task = tasks[0]
            context['selected_task'] = selected_task
            context['comments'] = selected_task.comments.select_related('author').all()
            context['files'] = selected_task.files.select_related('uploaded_by').all()
            context['is_author'] = selected_task.author == self.request.user
            context['is_assigned'] = self.request.user in selected_task.assigned_to.all()
            context['comment_form'] = TaskCommentForm()
            context['file_form'] = TaskFileForm()
        return context

@login_required
def task_board_detail_partial(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Permission check (reusing logic from DetailView)
    if task.author != request.user and request.user not in task.assigned_to.all():
        return HttpResponse("권한이 없습니다.", status=403)
        
    context = {
        'task': task,
        'comments': task.comments.select_related('author').all(),
        'files': task.files.select_related('uploaded_by').all(),
        'is_author': task.author == request.user,
        'is_assigned': request.user in task.assigned_to.all(),
        'comment_form': TaskCommentForm(),
        'file_form': TaskFileForm(),
    }
    html = render_to_string('task/task_detail_partial.html', context, request=request)
    return HttpResponse(html)

class TaskPlannerView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'task/task_planner.html'
    context_object_name = 'tasks'

    def get_base_queryset(self):
        """본인 업무/담당 업무, 연도, 카테고리 필터가 적용된 기본 쿼리셋을 반환 (상태 필터 제외)"""
        from django.utils import timezone
        
        include_prev_year = self.request.GET.get('include_prev_year') == 'true'
        date_type = self.request.GET.get('date_type', 'start_date')
        category_filter = [c for c in self.request.GET.getlist('category') if c]
        
        today = timezone.now().date()
        start_year = today.year
        if include_prev_year:
            start_year -= 1
        
        # 기본 권한 필터링 (본인 작성 또는 담당자)
        queryset = Task.objects.filter(
            Q(author=self.request.user) | Q(assigned_to=self.request.user)
        ).distinct()

        # 기간 필터링
        if date_type == 'start_date':
            queryset = queryset.filter(
                Q(start_date__year__gte=start_year) | Q(due_date__year__gte=start_year)
            )
        else:
            queryset = queryset.filter(created_at__year__gte=start_year)

        # 카테고리 필터링
        if category_filter:
            queryset = queryset.filter(category_id__in=category_filter)
        
        # '드랍' 상태는 전체 조회 및 카운트에서 제외
        queryset = queryset.exclude(status='dropped')
        
        return queryset

    def get_queryset(self):
        """최종 리스트를 위한 쿼리셋 (상태 필터 포함)"""
        queryset = self.get_base_queryset()
        
        # 상태 필터링
        status_filter = [s for s in self.request.GET.getlist('status') if s]
        if status_filter:
            queryset = queryset.filter(status__in=status_filter)
        
        return queryset.order_by('start_date', 'created_at').select_related('author', 'category', 'team').prefetch_related('assigned_to')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date
        today = date.today()
        
        include_prev_year = self.request.GET.get('include_prev_year') == 'true'
        years = [today.year]
        if include_prev_year:
            years = [today.year - 1, today.year]
        
        context['today'] = today
        context['years'] = years
        context['total_months'] = len(years) * 12
        context['current_statuses'] = [s for s in self.request.GET.getlist('status') if s]
        context['current_categories'] = [c for c in self.request.GET.getlist('category') if c]
        context['categories'] = Category.objects.all()
        context['include_prev_year'] = include_prev_year
        context['date_type'] = self.request.GET.get('date_type', 'start_date')
        
        # 상태별 카운트 계산 (상태 필터만 제외된 베이스 쿼리셋 기준)
        base_qs = self.get_base_queryset()
        counts_data = base_qs.values('status').annotate(count=Count('id', distinct=True))

        # 표시할 상태들에 대해 0으로 초기화
        status_counts = {'todo': 0, 'in_progress': 0, 'done': 0}
        total_sum = 0
        
        for item in counts_data:
            s_type = item['status']
            s_count = item['count']
            if s_type in status_counts:
                status_counts[s_type] += s_count
                total_sum += s_count
            
        status_counts['total'] = total_sum
        context['status_counts'] = status_counts
        
        return context

class TaskRoadmapView(TaskPlannerView):
    def get_base_queryset(self):
        """로드맵 모드에서는 Key Task만 필터링"""
        return super().get_base_queryset().filter(category__is_key_task=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_key_task=True)
        context['roadmap_mode'] = True
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'task/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # 파일 업로드 처리
        files = self.request.FILES.getlist('files')
        for f in files:
            TaskFile.objects.create(
                task=self.object,
                file=f,
                original_name=f.name,
                uploaded_by=self.request.user
            )

        # 담당자들에게 알림 생성 (새로운 알림 시스템 사용)
        assigned_users = form.instance.assigned_to.all()
        if assigned_users:
            notify_task_assigned(form.instance, assigned_users, self.request.user)
        
        messages.success(self.request, '업무가 성공적으로 생성되었습니다.')
        return response

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'task/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        # 작성자이거나 담당자로 지정된 업무들을 모두 조회하고 수정 가능
        return Task.objects.filter(
            Q(author=self.request.user) | Q(assigned_to=self.request.user)
        ).distinct()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # 작성자이거나 담당자인 경우 수정 가능
        if (form.instance.author != self.request.user and 
            self.request.user not in form.instance.assigned_to.all()):
            messages.error(self.request, '업무를 수정할 권한이 없습니다.')
            return redirect('task_detail', pk=form.instance.pk)
        
        previous_assigned_users = list(form.instance.assigned_to.all())
        response = super().form_valid(form)
        current_assigned_users = list(self.object.assigned_to.all())
        notify_task_assignment_changes(
            self.object,
            previous_assigned_users,
            current_assigned_users,
            self.request.user
        )
        
        # 파일 업로드 처리
        files = self.request.FILES.getlist('files')
        for f in files:
            TaskFile.objects.create(
                task=self.object,
                file=f,
                original_name=f.name,
                uploaded_by=self.request.user
            )

        messages.success(self.request, '업무가 성공적으로 수정되었습니다.')
        return response

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'task/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        # 작성자이거나 담당자인 경우 삭제 가능
        return Task.objects.filter(
            Q(author=self.request.user) | Q(assigned_to=self.request.user)
        ).distinct()

    def delete(self, request, *args, **kwargs):
        # 권한 체크
        task = self.get_object()
        if (task.author != request.user and 
            request.user not in task.assigned_to.all()):
            messages.error(request, '업무를 삭제할 권한이 없습니다.')
            return redirect('task_detail', pk=task.pk)
            
        messages.success(request, '업무가 성공적으로 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)

@login_required
def add_comment(request, task_id):
    """업무에 댓글 추가"""
    task = get_object_or_404(Task, id=task_id)
    
    # 권한 확인 (작성자 또는 담당자만 댓글 작성 가능)
    if task.author != request.user and request.user not in task.assigned_to.all():
        messages.error(request, '댓글을 작성할 권한이 없습니다.')
        return redirect('task_detail', pk=task_id)
    
    if request.method == 'POST':
        form = TaskCommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            
            # 댓글 추가 알림 (새로운 알림 시스템 사용)
            notify_comment_added(task, request.user, comment.content)
            
            messages.success(request, '댓글이 추가되었습니다.')
    
    return redirect('task_detail', pk=task_id)

@login_required
def delete_file(request, file_id):
    """업무 첨부파일 삭제"""
    task_file = get_object_or_404(TaskFile, id=file_id)
    task = task_file.task
    
    # 권한 확인 (작성자, 파일 업로드자, 또는 담당자가 삭제 가능)
    has_permission = (
        task.author == request.user or 
        task_file.uploaded_by == request.user or
        request.user in task.assigned_to.all()
    )
    
    if not has_permission:
        messages.error(request, '파일을 삭제할 권한이 없습니다.')
        return redirect('task_detail', pk=task.id)
    
    try:
        task_file.file.delete()  # 실제 파일 삭제
        task_file.delete()  # DB 레코드 삭제
        messages.success(request, '파일이 삭제되었습니다.')
    except Exception as e:
        messages.error(request, '파일 삭제 중 오류가 발생했습니다.')
    
    return redirect('task_detail', pk=task.id)

@login_required
def upload_file(request, task_id):
    """업무에 파일 업로드"""
    task = get_object_or_404(Task, id=task_id)
    
    # 권한 확인 (작성자 또는 담당자만 파일 업로드 가능)
    if task.author != request.user and request.user not in task.assigned_to.all():
        messages.error(request, '파일을 업로드할 권한이 없습니다.')
        return redirect('task_detail', pk=task_id)
    
    if request.method == 'POST':
        form = TaskFileForm(request.POST, request.FILES)
        if form.is_valid():
            task_file = form.save(commit=False)
            task_file.task = task
            task_file.uploaded_by = request.user
            task_file.original_name = request.FILES['file'].name
            task_file.save()
            
            messages.success(request, '파일이 업로드되었습니다.')
        else:
            messages.error(request, '파일 업로드에 실패했습니다.')
    
    return redirect('task_detail', pk=task_id)

@login_required
def download_file(request, file_id):
    """파일 다운로드"""
    task_file = get_object_or_404(TaskFile, id=file_id)
    task = task_file.task
    
    # 권한 확인 (작성자, 담당자, 또는 같은 팀 멤버)
    has_permission = (
        task.author == request.user or 
        request.user in task.assigned_to.all() or
        (task.team and request.user in task.team.members.all())
    )
    
    if not has_permission:
        messages.error(request, '파일을 다운로드할 권한이 없습니다.')
        return redirect('task_detail', pk=task.id)
    
    try:
        from django.http import FileResponse
        import mimetypes
        
        # Open file in binary mode
        file_handle = task_file.file.open('rb')
        
        # MIME 타입 자동 감지
        content_type, _ = mimetypes.guess_type(task_file.original_name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        response = FileResponse(file_handle, content_type=content_type, as_attachment=True, filename=task_file.original_name)
        return response
    except Exception as e:
        messages.error(request, '파일 다운로드 중 오류가 발생했습니다.')
        return redirect('task_detail', pk=task.id)

@login_required
def download_comment_file(request, comment_id):
    """댓글 첨부파일 다운로드"""
    comment = get_object_or_404(TaskComment, id=comment_id)
    if not comment.file:
        messages.error(request, '첨부파일이 없습니다.')
        return redirect('task_detail', pk=comment.task.id)
        
    task = comment.task
    # Permission check (author, assigned, or team member)
    has_permission = (
        task.author == request.user or 
        request.user in task.assigned_to.all() or
        (task.team and request.user in task.team.members.all())
    )
    
    if not has_permission:
        messages.error(request, '파일을 다운로드할 권한이 없습니다.')
        return redirect('task_detail', pk=task.id)
        
    try:
        from django.http import FileResponse
        import mimetypes
        import os
        
        file_handle = comment.file.open('rb')
        original_name = os.path.basename(comment.file.name)
        
        content_type, _ = mimetypes.guess_type(original_name)
        if not content_type:
            content_type = 'application/octet-stream'
            
        response = FileResponse(file_handle, content_type=content_type, as_attachment=True, filename=original_name)
        return response
    except Exception as e:
        messages.error(request, '파일 다운로드 중 오류가 발생했습니다.')
        return redirect('task_detail', pk=task.id)

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'task/category_list.html'
    context_object_name = 'categories'

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'task/category_form.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        messages.success(self.request, '카테고리가 생성되었습니다.')
        return super().form_valid(form)

@login_required
def task_status_update(request, task_id):
    """AJAX로 업무 상태 업데이트"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        
        # 권한 체크 (작성자 또는 담당자만 상태 변경 가능)
        if request.user != task.author and request.user not in task.assigned_to.all():
            return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
        
        old_status = task.status
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            
            # 상태 변경 알림
            if old_status != new_status:
                notify_task_status_changed(task, old_status, new_status, request.user)
                
                # 상태 변경 내역을 코멘트로 자동 추가
                status_display_map = dict(Task.STATUS_CHOICES)
                old_status_display = status_display_map.get(old_status, old_status)
                new_status_display = status_display_map.get(new_status, new_status)
                
                comment_content = f"📌 업무 상태가 변경되었습니다.\n• 변경 전: {old_status_display}\n• 변경 후: {new_status_display}\n• 변경자: {request.user.profile.display_name if hasattr(request.user, 'profile') and request.user.profile.display_name else request.user.username}"
                
                TaskComment.objects.create(
                    task=task,
                    author=request.user,
                    content=comment_content
                )
            
            return JsonResponse({
                'success': True, 
                'status': task.get_status_display(),
                'message': '업무 상태가 변경되었습니다.'
            })
    
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})
