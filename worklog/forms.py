from django import forms
from django.contrib.auth.models import User
from django.db import models
from .models import Worklog, WorklogFile, WorklogTask
from task.models import Task
import datetime

class WorklogForm(forms.ModelForm):
    class Meta:
        model = Worklog
        fields = ['this_week_work', 'next_week_plan', 'display_order']
        widgets = {
            'this_week_work': forms.Textarea(attrs={
                'class': 'form-control summernote', 
                'id': 'this_week_work',
                'rows': 15,
                'placeholder': '이번 주에 수행한 업무를 마크다운 형식으로 작성하세요...\n\n예시:\n## 주요 업무\n- ✅ **완료된 업무** [높음]\n- 🔄 **진행중인 업무**\n- 📋 **계획된 업무**\n\n### 상세 내용\n**중요한 내용**은 굵게 표시\n\n```python\n# 코드 블록도 사용 가능\nprint("Hello World")\n```'
            }),
            'next_week_plan': forms.Textarea(attrs={
                'class': 'form-control markdown-editor', 
                'id': 'next_week_plan',
                'rows': 15,
                'placeholder': '다음 주 계획을 마크다운 형식으로 작성하세요...\n\n예시:\n## 다음 주 계획\n1. 새로운 기능 개발\n2. 버그 수정\n3. 문서 작성\n\n> 중요: 우선순위가 높은 업무부터 처리'
            }),
            'display_order': forms.HiddenInput(),
        }
        labels = {
            'this_week_work': '이번 주 수행 업무 (마크다운)',
            'next_week_plan': '다음 주 계획 (마크다운)',
            'display_order': '표시 순서',
        }

    def __init__(self, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        user = kwargs.pop('user', None)
        logger.info(f"WorklogForm __init__ called with args: {len(args)}, kwargs: {list(kwargs.keys())}, user: {user}")
        
        try:
            super().__init__(*args, **kwargs)
            
            # 새 워크로그인 경우 사용자 프로필의 기본 순서 적용
            if user and not self.instance.pk:
                try:
                    if hasattr(user, 'profile') and user.profile:
                        self.fields['display_order'].initial = user.profile.default_display_order
                        logger.info(f"Set initial display_order from profile: {user.profile.default_display_order}")
                    else:
                        logger.warning("User has no profile, using default display_order=0")
                        self.fields['display_order'].initial = 0
                except Exception as e:
                    logger.error(f"Error setting initial display_order: {str(e)}")
                    self.fields['display_order'].initial = 0
            
            logger.info("WorklogForm initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing WorklogForm: {str(e)}", exc_info=True)
            raise

    def save(self, commit=True):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"WorklogForm save called, commit={commit}")
            instance = super().save(commit=False)
            logger.info(f"Instance created: author={getattr(instance, 'author', 'None')}, year={getattr(instance, 'year', 'None')}, week={getattr(instance, 'week_number', 'None')}")
            
            if commit:
                instance.save()
                logger.info("Instance saved to database")
            return instance
        except Exception as e:
            logger.error(f"Error saving WorklogForm: {str(e)}", exc_info=True)
            raise

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
