from django.db import models
from django.contrib.auth.models import User
import uuid
import hashlib
import json
from django.utils import timezone

class WebhookSource(models.Model):
    name = models.CharField(max_length=100, verbose_name="소스 이름")
    source_type = models.CharField(max_length=50, default='whatap', verbose_name="소스 유형")
    source_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="소스 키")
    secret_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="비밀 토큰")
    is_active = models.BooleanField(default=True, verbose_name="활성 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    
    class Meta:
        verbose_name = "웹훅 소스"
        verbose_name_plural = "웹훅 소스"

    def __str__(self):
        return f"{self.name} ({self.source_type})"

class WebhookEvent(models.Model):
    source = models.ForeignKey(WebhookSource, on_delete=models.CASCADE, related_name='events', verbose_name="소스")
    payload = models.JSONField(verbose_name="페이로드")
    headers = models.JSONField(blank=True, null=True, verbose_name="헤더")
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="수신일시")
    processed = models.BooleanField(default=False, verbose_name="처리 여부")
    external_uuid = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="외부 UUID")
    
    class Meta:
        verbose_name = "웹훅 이벤트"
        verbose_name_plural = "웹훅 이벤트"
        ordering = ['-received_at']

class Incident(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('fatal', 'Fatal'),
    ]
    
    title = models.CharField(max_length=255, verbose_name="제목")
    description = models.TextField(blank=True, verbose_name="설명")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="상태")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='warning', verbose_name="심각도")
    fingerprint = models.CharField(max_length=255, unique=True, verbose_name="지문(Dedupe Key)")
    source = models.ForeignKey(WebhookSource, on_delete=models.SET_NULL, null=True, verbose_name="소스")
    
    projectName = models.CharField(max_length=255, blank=True, verbose_name="프로젝트명")
    oname = models.CharField(max_length=255, blank=True, verbose_name="대상 이름")
    metricName = models.CharField(max_length=255, blank=True, verbose_name="메트릭명")
    
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents', verbose_name="담당자")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="해결일시")

    class Meta:
        verbose_name = "인시던트"
        verbose_name_plural = "인시던트"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class IncidentEvent(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='events', verbose_name="인시던트")
    event_type = models.CharField(max_length=50, verbose_name="이벤트 유형")
    message = models.TextField(verbose_name="메시지")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="발생일시")
    raw_event = models.ForeignKey(WebhookEvent, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="원본 이벤트")

    class Meta:
        verbose_name = "인시던트 이벤트"
        verbose_name_plural = "인시던트 이벤트"
        ordering = ['created_at']
