from django import forms
from django.contrib.auth.models import User
from .models import Task, Category, TaskComment, TaskFile

class TaskForm(forms.ModelForm):
    assigned_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label="담당자",
        required=False
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'category', 'due_date', 'team', 'assigned_to','progress']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '업무명을 입력하세요'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '업무 설명을 입력하세요'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'progress': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'min': 0, 'max': 100, 'step': 5}),
            'team': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # 사용자가 속한 팀만 표시
            self.fields['team'].queryset = user.teams.all()
            
            # 팀 멤버들만 담당자로 선택 가능
            if self.instance.team:
                self.fields['assigned_to'].queryset = self.instance.team.members.all()
            else:
                # 팀이 선택되지 않은 경우, 사용자가 속한 모든 팀의 멤버를 보여주거나,
                # 혹은 사용자와 같은 팀의 멤버만 보여주는 등의 정책이 필요합니다.
                # 여기서는 사용자가 속한 팀의 멤버들을 보여주도록 하겠습니다.
                user_teams = user.teams.all()
                self.fields['assigned_to'].queryset = User.objects.filter(teams__in=user_teams).distinct()

        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.profile.get_korean_name} ({obj.profile.position})"


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '카테고리명'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '댓글을 입력하세요'}),
        }

class TaskFileForm(forms.ModelForm):
    class Meta:
        model = TaskFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TaskSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '업무 검색...',
        }),
        required=False
    )
    status = forms.ChoiceField(
        choices=[('', '모든 상태')] + list(Task.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    priority = forms.ChoiceField(
        choices=[('', '모든 우선순위')] + list(Task.PRIORITY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        empty_label="모든 카테고리"
    )
