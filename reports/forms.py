from django import forms
from .models import WeeklyReportComment, WeeklyReportPersonalComment
from teams.models import Team
import datetime

class WeeklyReportCommentForm(forms.ModelForm):
    class Meta:
        model = WeeklyReportComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '주간 리포트에 대한 코멘트를 작성하세요...'
            }),
        }
        labels = {
            'content': '코멘트'
        }


class WeeklyReportPersonalCommentForm(forms.ModelForm):
    class Meta:
        model = WeeklyReportPersonalComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '담당자에게 전달할 업무 코멘트를 입력하세요.',
                'id': 'personalCommentContent'
            }),
        }
        labels = {
            'content': '업무 코멘트'
        }
