from django import forms
from django.contrib.auth.models import User
from django.db import models
from .models import Worklog, WorklogFile
from task.models import Task
import datetime

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

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

    files = forms.FileField(
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        label='첨부파일',
        required=False
    )

    def __init__(self, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        user = kwargs.pop('user', None)
        self.user = user
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
                
                # 파일 처리
                if self.files:
                    files = self.files.getlist('files')
                    for f in files:
                        WorklogFile.objects.create(
                            worklog=instance,
                            file=f,
                            original_name=f.name,
                            uploaded_by=self.user or instance.author
                        )
                    logger.info(f"Saved {len(files)} files for worklog {instance.pk}")
                    
            return instance
        except Exception as e:
            logger.error(f"Error saving WorklogForm: {str(e)}", exc_info=True)
            raise


class WorklogFileForm(forms.ModelForm):
    class Meta:
        model = WorklogFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
