from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from teams.models import Team, TeamMembership

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['last_name_ko', 'first_name_ko', 'position', 'phone']
        widgets = {
            'last_name_ko': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '홍'}),
            'first_name_ko': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '길동'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '대리'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '010-1234-5678'}),
        }
        labels = {
            'last_name_ko': '성',
            'first_name_ko': '이름',
            'position': '직급',
            'phone': '전화번호',
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
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
        widget=forms.Select(attrs={'class': 'form-control'})
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

class UserEditForm(forms.Form):
    """사용자 수정을 위한 통합 폼"""
    # 기본 사용자 정보
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label='이름 (영문)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label='성 (영문)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label='이메일',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    # 프로필 정보
    last_name_ko = forms.CharField(
        max_length=10,
        required=False,
        label='성 (한글)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '홍'})
    )
    first_name_ko = forms.CharField(
        max_length=20,
        required=False,
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # 기본 사용자 정보 초기값 설정
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            self.fields['is_staff'].initial = self.user.is_staff
            self.fields['is_superuser'].initial = self.user.is_superuser
            
            # 프로필 정보 초기값 설정
            if hasattr(self.user, 'profile'):
                profile = self.user.profile
                self.fields['last_name_ko'].initial = profile.last_name_ko
                self.fields['first_name_ko'].initial = profile.first_name_ko
                self.fields['position'].initial = profile.position
                self.fields['phone'].initial = profile.phone
            
            # 권한 그룹 초기값 설정
            self.fields['groups'].initial = self.user.groups.all()
            
            # 팀 초기값 설정
            self.fields['teams'].initial = self.user.teams.all()

    def save(self):
        if not self.user:
            return None
        
        # 기본 사용자 정보 업데이트
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.is_staff = self.cleaned_data['is_staff']
        self.user.is_superuser = self.cleaned_data['is_superuser']
        self.user.save()
        
        # 프로필 정보 업데이트
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.last_name_ko = self.cleaned_data['last_name_ko']
        profile.first_name_ko = self.cleaned_data['first_name_ko']
        profile.position = self.cleaned_data['position']
        profile.phone = self.cleaned_data['phone']
        profile.save()
        
        # 권한 그룹 업데이트
        self.user.groups.set(self.cleaned_data['groups'])
        
        # 팀 멤버십 업데이트
        # 기존 멤버십 삭제
        TeamMembership.objects.filter(user=self.user).delete()
        
        # 새로운 멤버십 생성
        for team in self.cleaned_data['teams']:
            TeamMembership.objects.create(
                team=team,
                user=self.user,
                role='member'  # 기본값으로 멤버 설정
            )
        
        return self.user

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
