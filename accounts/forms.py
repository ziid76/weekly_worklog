from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from teams.models import Team, TeamMembership

class UserProfileForm(forms.ModelForm):
    team_role = forms.ChoiceField(
        choices=TeamMembership.ROLE_CHOICES,
        initial='member',
        label='팀 내 역할',
        widget=forms.RadioSelect
    )

    class Meta:
        model = UserProfile
        fields = ['last_name_ko', 'first_name_ko', 'position', 'phone', 'team_role']
        widgets = {
            'last_name_ko': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '홍'}),
            'first_name_ko': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '길동'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '대리'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '010-1234-5678'}),
            'team_role': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }
        labels = {
            'last_name_ko': '성',
            'first_name_ko': '이름',
            'position': '직급',
            'phone': '전화번호',
            'team_role': '팀 내 역할'
        }

class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(required=True,
        label='사용자 ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': '이름 (영문)',
            'last_name': '성 (영문)',
            'email': '이메일',
        }

class UserCreationFormWithProfile(UserCreationForm):
    """사용자 생성 폼 (프로필 정보 포함)"""
    password1 = forms.CharField(required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doe'})
    )
    
    # 프로필 필드들
    last_name_ko = forms.CharField(
        max_length=10,
        required=True,
        label='성 (한글)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '홍'})
    )
    first_name_ko = forms.CharField(
        max_length=20,
        required=True,
        label='이름 (한글)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '길동'})
    )
    position = forms.CharField(
        max_length=30,
        required=False,
        label='직급',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '대리'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='전화번호',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '010-1234-5678'})
    )
    
    # 권한 설정
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='권한 그룹',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    # 팀 설정
    teams = forms.ModelMultipleChoiceField(
        queryset=Team.objects.all(),
        required=False,
        label='소속 팀',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    # 팀 역할
    team_role = forms.ChoiceField(
        choices=TeamMembership.ROLE_CHOICES,
        initial='member',
        label='팀 내 역할',
        widget=forms.RadioSelect
    )
    
    # 관리자 권한
    is_staff = forms.BooleanField(
        required=False,
        label='관리자 권한',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_superuser = forms.BooleanField(
        required=False,
        label='슈퍼유저 권한',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.TextInput(attrs={'class': 'form-control'}),
            'password2': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = self.cleaned_data['is_staff']
        user.is_superuser = self.cleaned_data['is_superuser']
        
        if commit:
            user.save()
            
            # 프로필 생성
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.last_name_ko = self.cleaned_data['last_name_ko']
            profile.first_name_ko = self.cleaned_data['first_name_ko']
            profile.position = self.cleaned_data['position']
            profile.phone = self.cleaned_data['phone']
            profile.save()
            
            # 권한 그룹 설정
            if self.cleaned_data['groups']:
                user.groups.set(self.cleaned_data['groups'])
            
            # 팀 설정
            if self.cleaned_data['teams']:
                team_role = self.cleaned_data['team_role']
                for team in self.cleaned_data['teams']:
                    TeamMembership.objects.create(
                        team=team,
                        user=user,
                        role=team_role
                    )
        
        return user



class TeamCreationForm(forms.ModelForm):
    """팀 생성 폼"""
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '개발팀'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '팀에 대한 설명을 입력하세요'}),
        }
        labels = {
            'name': '팀명',
            'description': '팀 설명',
        }
