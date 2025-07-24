from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from teams.models import TeamMembership

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    last_name_ko = models.CharField("성", max_length=10, blank=True)
    first_name_ko = models.CharField("이름", max_length=20, blank=True)
    position = models.CharField("직급", max_length=30, blank=True)
    phone = models.CharField("전화번호", max_length=20, blank=True)
    team_role = models.CharField("팀 내 역할", max_length=20, choices=TeamMembership.ROLE_CHOICES, default='member', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_korean_name}"

    @property
    def get_korean_name(self):
        """한국식 성이름 형식으로 반환"""
        if self.last_name_ko and self.first_name_ko:
            return f"{self.last_name_ko}{self.first_name_ko}"
        elif self.user.last_name and self.user.first_name:
            return f"{self.user.last_name}{self.user.first_name}"
        else:
            return self.user.username

    @property
    def display_name(self):
        """화면 표시용 이름"""
        korean_name = self.get_korean_name
        if korean_name != self.user.username:
            if self.user.profile.position:
                return f"{korean_name} ({self.user.profile.position})"
            else: return f"{korean_name} "
        return self.user.username

    @property
    def task_count(self):
        """Task 수 반환"""
        from task.models import Task
        cnt = Task.objects.filter(author=self.user).count()
        return cnt
    
    @property
    def primary_team(self):
        """사용자의 주요 팀 반환 (첫 번째 팀 또는 팀장인 팀)"""
        from teams.models import TeamMembership
        
        # 팀장인 팀이 있으면 우선 반환
        leader_membership = TeamMembership.objects.filter(
            user=self.user, 
            role='leader'
        ).select_related('team').first()
        
        if leader_membership:
            return leader_membership.team
        
        # 그 외에는 첫 번째 팀 반환
        first_membership = TeamMembership.objects.filter(
            user=self.user
        ).select_related('team').first()
        
        return first_membership.team if first_membership else None

    @property
    def team_names(self):
        """사용자가 속한 모든 팀 이름들을 문자열로 반환"""
        teams = self.user.teams.all()
        if teams:
            return ", ".join([team.name for team in teams])
        return "미배정"

    @property
    def department_display(self):
        """부서 정보 대신 팀 정보 반환 (하위 호환성)"""
        return self.primary_team.name if self.primary_team else "미배정"

# User 생성 시 자동으로 UserProfile 생성
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)
