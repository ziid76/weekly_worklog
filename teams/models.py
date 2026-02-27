from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField("팀명", max_length=100)
    description = models.TextField("팀 설명", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    members = models.ManyToManyField(User, through='TeamMembership', related_name='teams')
    is_sr_team = models.BooleanField("SR 접수 처리 팀 여부", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TeamMembership(models.Model):
    ROLE_CHOICES = (
        ('member', '멤버'),
        ('leader', '팀장'),
        ('admin', '관리자'),
    )

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField("역할", max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.team.name} ({self.role})'
