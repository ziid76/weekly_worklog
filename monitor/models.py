from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class LogCategory(models.Model):
    """Log category for operation logs"""
    name = models.CharField(max_length=100, verbose_name="카테고리명")
    code = models.CharField(max_length=50, unique=True, verbose_name="카테고리 코드")
    description = models.TextField(blank=True, verbose_name="설명")
    order = models.IntegerField(default=0, verbose_name="정렬 순서")
    is_active = models.BooleanField(default=True, verbose_name="활성화")
    
    class Meta:
        verbose_name = "로그 카테고리"
        verbose_name_plural = "로그 카테고리"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class LogSubcategory(models.Model):
    """Log subcategory for operation logs"""
    category = models.ForeignKey(LogCategory, on_delete=models.CASCADE, related_name='subcategories', verbose_name="카테고리")
    name = models.CharField(max_length=100, verbose_name="하위 카테고리명")
    code = models.CharField(max_length=50, verbose_name="하위 카테고리 코드")
    description = models.TextField(blank=True, verbose_name="설명")
    order = models.IntegerField(default=0, verbose_name="정렬 순서")
    is_active = models.BooleanField(default=True, verbose_name="활성화")
    
    class Meta:
        verbose_name = "로그 하위 카테고리"
        verbose_name_plural = "로그 하위 카테고리"
        ordering = ['category', 'order', 'name']
        unique_together = ['category', 'code']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class OperationLog(models.Model):
    """System operation log with multiple checks"""
    date = models.DateField()
    duty_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='duty_operation_logs')
    completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_operation_logs')
    completed_at = models.DateTimeField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_operation_logs')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "운영 로그"
        verbose_name_plural = "운영 로그"
        ordering = ['-date']
    
    def __str__(self):
        return f"운영 로그 {self.date}"
    
    def check_complete(self):
        # Get all active categories
        categories = LogCategory.objects.filter(is_active=True)
        
        # Check if all categories have completed log entries
        for category in categories:
            log_entries = self.log_entries.filter(category=category)
            if not log_entries.exists() or not any(entry.is_checked for entry in log_entries):
                return False
        
        return True
    
    def check_start(self):
        # Check if any log entry exists and is checked
        return self.log_entries.filter(is_checked=True).exists()
    
    def finalize(self, user):
        if self.check_complete():
            self.completed = True
            self.completed_by = user
            self.completed_at = timezone.now()
            self.save()
            return True
        return False


class LogEntry(models.Model):
    """Individual log entry for a specific category"""
    operation_log = models.ForeignKey(OperationLog, on_delete=models.CASCADE, related_name='log_entries')
    category = models.ForeignKey(LogCategory, on_delete=models.CASCADE, related_name='log_entries')
    result = models.TextField(blank=True, verbose_name="점검 결과")
    has_trouble = models.BooleanField(default=False, verbose_name="문제")
    is_checked = models.BooleanField(default=False, verbose_name="점검완료")
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='log_entries')
    checked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "로그 항목"
        verbose_name_plural = "로그 항목"
        unique_together = ['operation_log', 'category']
    
    def __str__(self):
        return f"{self.operation_log.date} - {self.category.name}"


class SubcategoryEntry(models.Model):
    """Individual subcategory entry for a log entry"""
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name='subcategory_entries')
    subcategory = models.ForeignKey(LogSubcategory, on_delete=models.CASCADE, related_name='entries')
    result = models.TextField(blank=True, verbose_name="점검 결과")
    has_trouble = models.BooleanField(default=False, verbose_name="문제")
    is_checked = models.BooleanField(default=False, verbose_name="점검완료")
    
    class Meta:
        verbose_name = "하위 카테고리 항목"
        verbose_name_plural = "하위 카테고리 항목"
        unique_together = ['log_entry', 'subcategory']
    
    def __str__(self):
        return f"{self.log_entry.operation_log.date} - {self.log_entry.category.name} - {self.subcategory.name}"


def operation_directory_path(instance, filename):
    return 'op_attatchment/{0}/{1}'.format(instance.record.id, filename)


class OperationLogAttachment(models.Model):
    record = models.ForeignKey(OperationLog, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to=operation_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
