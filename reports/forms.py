from django import forms
from .models import WeeklyReportComment, TeamWeeklyReport
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

class TeamWeeklyReportForm(forms.ModelForm):
    class Meta:
        model = TeamWeeklyReport
        fields = ['team', 'year', 'week_number', 'title', 'summary', 'achievements', 'issues', 'next_week_plan']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020, 'max': 2030}),
            'week_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 53}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '리포트 제목을 입력하세요'}),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '이번 주 전반적인 업무 요약을 작성하세요...'
            }),
            'achievements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '이번 주 주요 성과와 완료된 업무를 작성하세요...'
            }),
            'issues': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '발생한 이슈나 문제점, 해결 방안을 작성하세요...'
            }),
            'next_week_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '다음 주 계획과 목표를 작성하세요...'
            }),
        }
        labels = {
            'team': '팀',
            'year': '년도',
            'week_number': '주차',
            'title': '리포트 제목',
            'summary': '주간 요약',
            'achievements': '주요 성과',
            'issues': '이슈 및 문제점',
            'next_week_plan': '다음 주 계획',
        }

    def __init__(self, *args, **kwargs):
        available_teams = kwargs.pop('available_teams', Team.objects.none())
        super().__init__(*args, **kwargs)
        
        # 사용자가 접근 가능한 팀만 선택지로 제공
        self.fields['team'].queryset = available_teams
        
        # 현재 주차 정보로 초기값 설정
        if not self.instance.pk:
            today = datetime.date.today()
            current_year, current_week, _ = today.isocalendar()
            self.fields['year'].initial = current_year
            self.fields['week_number'].initial = current_week

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        year = cleaned_data.get('year')
        week_number = cleaned_data.get('week_number')
        
        # 동일한 팀, 년도, 주차의 리포트가 이미 존재하는지 확인 (수정 시 제외)
        if team and year and week_number:
            existing_report = TeamWeeklyReport.objects.filter(
                team=team,
                year=year,
                week_number=week_number
            )
            
            # 수정 시에는 현재 인스턴스 제외
            if self.instance.pk:
                existing_report = existing_report.exclude(pk=self.instance.pk)
            
            if existing_report.exists():
                raise forms.ValidationError(
                    f'{team.name} 팀의 {year}년 {week_number}주차 리포트가 이미 존재합니다.'
                )
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 제목이 비어있으면 자동 생성
        if not instance.title:
            instance.title = f'{instance.team.name} - {instance.year}년 {instance.week_number}주차 리포트'
        
        if commit:
            instance.save()
        
        return instance
