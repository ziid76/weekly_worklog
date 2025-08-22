from django.db import models
from django.contrib.auth.models import User
from datetime import date
import uuid

# Create your models here.
class CommonCode(models.Model):
    """Hierarchical common code table with parent-level group and description."""
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')  # Parent code
    group = models.CharField(max_length=50, blank=True, null=True) # Allow null for leaf nodes
    description = models.TextField(blank=True, null=True) # Allow null for leaf nodes
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    dataset = models.CharField(max_length=255,blank=True, null=True)
    active = models.BooleanField(default=True)
    

    class Meta:
        unique_together = ('parent', 'group', 'code')

    def __str__(self):
        return f"{self.name}"

    def get_parent_group(self):
        if self.parent:
            return self.parent.group
        return None

    def get_parent_description(self):
        if self.parent:
            return self.parent.description
        return None



class ServiceRequest(models.Model):

    S_CHOICES=(
        ("N", "요청접수"),
        ("P", "처리중"),
        ("G", "처리완료"),
        ("D", "처리불가")
    )

    parent_sr = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_srs', verbose_name='원 SR') # 원본 SR과 파생 SR 간의 관계 정의
    req_user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True) #요청자
    req_type = models.ForeignKey('CommonCode', on_delete=models.SET_NULL, null=True) # 요청유형
    req_title = models.TextField(verbose_name='제목', blank=True)  
    req_system = models.TextField(verbose_name='요청시스템', null=True, blank=True)  
    req_module = models.TextField(verbose_name='요청모듈', null=True, blank=True) 
    req_depart = models.TextField(verbose_name='요청부서', blank=True)  
    req_name =  models.TextField(verbose_name='요청자', blank=True)  
    req_email =  models.TextField(verbose_name='요청자 email', blank=True) 
    req_reason = models.TextField(verbose_name='요청사유', blank=True)  # Allow blank
    req_details = models.TextField(verbose_name='요청내용', blank=True) # Allow blank
    rcv_opinion = models.TextField(verbose_name='담당부서의견', blank=True) # Allow blank
    date_of_req = models.DateField(verbose_name='희망적용일자', null=True, blank=True)
    date_of_recept = models.DateField(verbose_name='접수일자', auto_now_add=True)
    split_msg = models.TextField(verbose_name='분할메시지', blank=True)
    split_date_of_due = models.DateField(verbose_name='분할SR완료요청일자', null=True, blank=True)
    date_of_due = models.DateField(verbose_name='완료예정일자', null=True, blank=True)
    date_of_complete = models.DateField(verbose_name='완료일자', null=True, blank=True)
    complete_content = models.TextField(verbose_name='처리결과', blank=True) # Allow blank
    reject_reason = models.TextField(verbose_name='처리결과', blank=True) # Allow blank
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests', verbose_name='담당자')
    effort_expected = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='예상 작업 시간(M/H)', blank=True, null=True) # Example: 2.5 hours
    effort = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='예상 작업 시간(M/H)', blank=True, null=True) # Example: 2.5 hours
    status = models.CharField(choices=S_CHOICES, default="N", max_length=1, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_parent(self):
        """SR이 분할 SR을 가지고 있는지 확인"""
        return self.child_srs.exists()
    
    def is_child(self):
        """SR이 다른 SR의 분할SR인지 확인"""
        return self.parent_sr is not None
    
    def is_root(self):
        """원본 SR인지 확인"""
        if not self.parent_sr:
            return True
        return False

    def get_root_sr(self):
        """최상위 원본 SR 찾기"""
        if not self.parent_sr:
            return self
        return self.parent_sr.get_root_sr()
    
    def get_parent_sr(self):
        """부모 SR 찾기"""
        if not self.parent_sr:
            return self
        return self.parent_sr
    
    def get_all_related_srs(self):
        """이 SR과 연관된 모든 SR 찾기 (형제 포함)"""
        if self.parent_sr:
            return self.parent_sr.child_srs.all()
        return self.child_srs.all()

    def get_status_text(self):
        """상태값 텍스트 변환"""
        if self.status == 'N':
            return "요청접수"
        elif self.status == 'P':
            return "처리중"
        elif self.status == 'G':
            return "처리완료"
        elif self.status == 'D':
            return "처리불가"
        
        return self.status

    def get_status_N(self):
        return self.steps.filter(status='N')

    def get_status_P(self):
        return self.steps.filter(status='P')
    
    def is_over_due(self):
        if self.date_of_due > date.today():
            return True
        return False
    

    def get_status_P(self):
        return self.steps.filter(status='P')
    
def service_directory_path(instance, filename):

    return 'sr_attatchment/{0}/{1}'.format(instance.record.id, filename)


class ServiceRequestAttachment(models.Model):
    record = models.ForeignKey(ServiceRequest, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to=service_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ServiceRequestStep(models.Model):
    S_CHOICES=(
        ("N", "요청접수"),
        ("P", "처리중"),
        ("G", "처리완료"),
        ("D", "처리불가")
    )
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="steps", verbose_name="서비스 요청")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="처리자")
    step_time = models.DateTimeField(auto_now_add=True, verbose_name="처리 시간")
    content = models.TextField(verbose_name="처리 내용")
    status = models.TextField(choices=S_CHOICES, verbose_name='처리상태', null=True, blank=True) 
        
    def get_steps_with_status(self, status_value): # 인자 status_value 추가

        if not self.service_request:
            # service_request가 없는 비정상적인 경우 빈 QuerySet 반환
            return ServiceRequestStep.objects.none()

        # Optional: 전달받은 status_value가 유효한지 확인
        valid_statuses = [choice[0] for choice in self.S_CHOICES]
        if status_value not in valid_statuses:
             # 유효하지 않으면 빈 QuerySet 반환 (또는 에러 발생)
             return ServiceRequestStep.objects.none()
             # raise ValueError(f"Invalid status value: {status_value}")

        return ServiceRequestStep.objects.filter(
            service_request=self.service_request,
            status=status_value # self.status 대신 인자로 받은 status_value 사용
        )
    def __str__(self):
        return f"{self.service_request.req_name} - {self.get_status_display()} - {self.step_time}"


class ServiceInspection(models.Model):
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="inspections", verbose_name="서비스 요청")
    seq = models.IntegerField(verbose_name="일련번호", null=True, blank=True)
    inspector_name = models.CharField(max_length=100, verbose_name="검수 담당자")
    inspector_email = models.EmailField(verbose_name="검수 담당자 이메일")
    dev_test_detail = models.TextField(verbose_name="개발담당자 테스트 내역")
    test_request = models.TextField(verbose_name="테스트 요청 사항")
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    test_result = models.TextField(verbose_name="테스트 결과", blank=True)
    RESULT_CHOICES = (
        ("C", "완료"),
        ("R", "재작업"),
    )
    result = models.CharField(max_length=1, choices=RESULT_CHOICES, null=True, blank=True, verbose_name="결과")
    result_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["seq"]

    def get_status_text(self):
        """Return human readable status"""
        if self.result == "C":
            return "검수 완료"
        elif self.result == "R":
            return "재작업 요청"
        return "검수 요청"

    def __str__(self):
        return f"Inspection for SR {self.service_request.id}"


class ServiceRelease(models.Model):
    """CTS/릴리즈 요청 내역"""
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="releases", verbose_name="서비스 요청")
    release_date = models.DateField(verbose_name="반영 요청일자")
    source_system = models.CharField(max_length=100, verbose_name="Source System")
    target_system = models.CharField(max_length=100, verbose_name="Target System")
    request_number = models.CharField(max_length=100, verbose_name="요청번호", blank=True)
    description = models.TextField(verbose_name="설명", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False, verbose_name="승인 여부")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_releases", verbose_name="승인자")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="승인 일시")

    def __str__(self):
        return f"Release for SR {self.service_request.id} ({self.request_number})"
