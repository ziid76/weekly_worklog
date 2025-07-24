from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone




class OperationLog(models.Model):
    """System operation log with multiple checks"""
    date = models.DateField()
    duty_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='duty_operation_logs')
    monitoring_result = models.TextField(blank=True)
    monitoring_yn = models.BooleanField(default=False, verbose_name="점검완료")
    monitoring_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='monitoring_operation_logs')
    monitoring_created_at = models.DateTimeField(null=True, blank=True)
    sap_backup_result = models.TextField(blank=True)
    sap_backup_yn = models.BooleanField(default=False, verbose_name="점검완료")
    sap_backup_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sap_backup_operation_logs')
    sap_backup_created_at = models.DateTimeField(null=True, blank=True)
    room_backup_result = models.TextField(blank=True)
    room_backup_yn = models.BooleanField(default=False, verbose_name="점검완료")
    room_backup_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='room_backup_operation_logs')
    room_backup_created_at = models.DateTimeField(null=True, blank=True)
    cloud_backup_result = models.TextField(blank=True)
    cloud_backup_yn = models.BooleanField(default=False, verbose_name="점검완료")
    cloud_backup_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cloud_backup_operation_logs')
    cloud_backup_created_at = models.DateTimeField(null=True, blank=True)
    offsite_backup_result = models.TextField(blank=True)
    offsite_backup_yn = models.BooleanField(default=False, verbose_name="점검완료")
    offsite_backup_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='offsite_backup_operation_logs')
    offsite_backup_created_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_operation_logs')
    completed_at = models.DateTimeField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_operation_logs')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def check_complete(self):
        fields = [
            self.monitoring_yn,
            self.sap_backup_yn,
            self.room_backup_yn,
            self.cloud_backup_yn,
            self.offsite_backup_yn,
        ]
        return all(bool(f) for f in fields)

    def check_start(self):
        fields = [
            self.monitoring_yn,
            self.sap_backup_yn,
            self.room_backup_yn,
            self.cloud_backup_yn,
            self.offsite_backup_yn,
        ]
        return any(bool(f) for f in fields)


    def finalize(self, user):
        if self.check_complete():
            self.completed = True
            self.completed_by = user
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
def operation_directory_path(instance, filename):

    return 'op_attatchment/{0}/{1}'.format(instance.record.id, filename)


class OperationLogAttachment(models.Model):
    record = models.ForeignKey(OperationLog, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to=operation_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
