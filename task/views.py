from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Task, Category, TaskComment, TaskFile
from .forms import TaskForm, CategoryForm, TaskCommentForm, TaskFileForm, TaskSearchForm
from notifications.utils import notify_task_assigned, notify_comment_added, notify_task_status_changed

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
        form = TaskSearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            status = form.cleaned_data.get('status')
            priority = form.cleaned_data.get('priority')
            category = form.cleaned_data.get('category')
            
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) | Q(description__icontains=query)
                )
            if status:
                queryset = queryset.filter(status=status)
            if priority:
                queryset = queryset.filter(priority=priority)
            if category:
                queryset = queryset.filter(category=category)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaskSearchForm(self.request.GET)
        context['categories'] = Category.objects.all()
        return context

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'task/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        # 작성자이거나 담당자로 지정된 업무들을 모두 조회
        return Task.objects.filter(
            Q(author=self.request.user) | Q(assigned_to=self.request.user)
        ).distinct().select_related('author', 'category', 'team').prefetch_related('assigned_to')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = TaskCommentForm()
        context['file_form'] = TaskFileForm()
        context['comments'] = self.object.comments.select_related('author').all()
        context['files'] = self.object.files.select_related('uploaded_by').all()
        
        # 현재 사용자가 이 업무의 작성자인지 담당자인지 구분
        context['is_author'] = self.object.author == self.request.user
        context['is_assigned'] = self.request.user in self.object.assigned_to.all()
        
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
        
        messages.success(self.request, '업무가 성공적으로 수정되었습니다.')
        return super().form_valid(form)

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
            notify_comment_added(task, request.user)
            
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
        import mimetypes
        from urllib.parse import quote
        
        # MIME 타입 자동 감지
        content_type, _ = mimetypes.guess_type(task_file.original_name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        response = HttpResponse(task_file.file.read(), content_type=content_type)
        
        # 파일명 인코딩 처리 (한글 및 특수문자 지원)
        encoded_filename = quote(task_file.original_name.encode('utf-8'))
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        
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
            
            return JsonResponse({
                'success': True, 
                'status': task.get_status_display(),
                'message': '업무 상태가 변경되었습니다.'
            })
    
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})