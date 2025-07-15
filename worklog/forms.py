from django import forms
from django.contrib.auth.models import User
from django.db import models
from .models import Worklog, WorklogFile, WorklogTask
from task.models import Task
import datetime

class WorklogForm(forms.ModelForm):
    class Meta:
        model = Worklog
        fields = ['this_week_work', 'next_week_plan']
        widgets = {
            'this_week_work': forms.Textarea(attrs={
                'class': 'form-control markdown-editor', 
                'rows': 15,
                'placeholder': '이번 주에 수행한 업무를 마크다운 형식으로 작성하세요...\n\n예시:\n## 주요 업무\n- ✅ **완료된 업무** [높음]\n- 🔄 **진행중인 업무**\n- 📋 **계획된 업무**\n\n### 상세 내용\n**중요한 내용**은 굵게 표시\n\n```python\n# 코드 블록도 사용 가능\nprint("Hello World")\n```'
            }),
            'next_week_plan': forms.Textarea(attrs={
                'class': 'form-control markdown-editor', 
                'rows': 15,
                'placeholder': '다음 주 계획을 마크다운 형식으로 작성하세요...\n\n예시:\n## 다음 주 계획\n1. 새로운 기능 개발\n2. 버그 수정\n3. 문서 작성\n\n> 중요: 우선순위가 높은 업무부터 처리'
            }),
        }
        labels = {
            'this_week_work': '이번 주 수행 업무 (마크다운)',
            'next_week_plan': '다음 주 계획 (마크다운)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

class WorklogTaskForm(forms.ModelForm):
    """워크로그에 Task를 추가하는 폼"""
    class Meta:
        model = WorklogTask
        fields = ['task', 'status', 'progress', 'time_spent', 'notes']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'progress': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 100,
                'placeholder': '0-100'
            }),
            'time_spent': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.5',
                'placeholder': '예: 2.5'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': '업무 진행 상황이나 특이사항을 입력하세요...'
            }),
        }
        labels = {
            'task': '업무',
            'status': '상태',
            'progress': '진행률 (%)',
            'time_spent': '소요 시간 (시간)',
            'notes': '비고',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        worklog = kwargs.pop('worklog', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # 사용자가 작성했거나 담당자로 지정된 업무들
            from django.db.models import Q
            user_tasks = Task.objects.filter(
                Q(author=user) | Q(assigned_to=user)
            ).distinct().order_by('-created_at')
            
            # 이미 워크로그에 추가된 업무는 제외
            if worklog:
                existing_task_ids = WorklogTask.objects.filter(
                    worklog=worklog
                ).values_list('task_id', flat=True)
                user_tasks = user_tasks.exclude(id__in=existing_task_ids)
            
            self.fields['task'].queryset = user_tasks
            
            # 업무가 없으면 빈 선택지 표시
            if not user_tasks.exists():
                self.fields['task'].empty_label = "추가할 수 있는 업무가 없습니다"

class WorklogFileForm(forms.ModelForm):
    class Meta:
        model = WorklogFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
