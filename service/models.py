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
    category = models.CharField(max_length=50, blank=True, null=True, verbose_name="카테고리명")
    display_order = models.IntegerField(default=0, verbose_name="표시 순서")
    active = models.BooleanField(default=True)
    separator = models.CharField(max_length=1, blank=True, null=True, verbose_name="구분자")
    

    class Meta:
        unique_together = ('parent', 'group', 'code')
        ordering = ['category', 'display_order', 'name']

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
        ("N", "서비스 생성"),
        ("A", "승인 대기"),
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
    req_depart = models.TextField(verbose_name='요청부서', null=True, blank=True)  
    req_name =  models.TextField(verbose_name='요청자', null=True, blank=True)  
    req_email =  models.TextField(verbose_name='요청자 email', null=True, blank=True) 
    req_reason = models.TextField(verbose_name='요청사유', null=True, blank=True)  # Allow blank
    req_details = models.TextField(verbose_name='요청내용', null=True, blank=True) # Allow blank
    rcv_opinion = models.TextField(verbose_name='담당부서의견',null=True,  blank=True) # Allow blank
    date_of_req = models.DateField(verbose_name='희망적용일자', null=True, blank=True)
    date_of_recept = models.DateField(verbose_name='접수일자', auto_now_add=True)
    split_msg = models.TextField(verbose_name='분할메시지', null=True, blank=True)
    split_date_of_due = models.DateField(verbose_name='분할SR완료요청일자', null=True, blank=True)
    date_of_due = models.DateField(verbose_name='완료예정일자', null=True, blank=True)
    date_of_complete = models.DateField(verbose_name='완료일자', null=True, blank=True)
    complete_content = models.TextField(verbose_name='처리결과', null=True, blank=True) # Allow blank
    reject_reason = models.TextField(verbose_name='처리결과', null=True, blank=True) # Allow blank
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
            return "서비스 생성"
        elif self.status == 'A':
            return "승인 대기"
        elif self.status == 'P':
            return "처리중"
        elif self.status == 'G':
            return "처리완료"
        elif self.status == 'D':
            return "처리불가"
        
        return self.status

    def get_status_N(self):
        return self.steps.filter(status='N')

    def get_status_A(self):
        return self.steps.filter(status='A')

    def get_status_P(self):
        return self.steps.filter(status='P').order_by('step_time')
    
    def get_req_attachments(self):
        return self.attachments.filter(file_type='REQ')

    def get_rcv_attachments(self):
        return self.attachments.filter(file_type='RCV')

    def get_step_attachments(self):
        return self.attachments.filter(file_type='STEP')

    def is_over_due(self):
        if self.date_of_due > date.today():
            return True
        return False
    
def service_directory_path(instance, filename):

    return 'sr_attatchment/{0}/{1}'.format(instance.record.id, filename)


class ServiceRequestAttachment(models.Model):
    TYPE_CHOICES = (
        ('REQ', '요청'),
        ('RCV', '접수'),
        ('STEP', '진행'),
    )
    record = models.ForeignKey(ServiceRequest, related_name='attachments', on_delete=models.CASCADE)
    step = models.ForeignKey('ServiceRequestStep', related_name='attachments', on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to=service_directory_path)
    file_type = models.CharField(max_length=4, choices=TYPE_CHOICES, default='REQ')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_file_type_display()}] {self.file.name}"


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


class ServiceRequestFormData(models.Model):
    """동적 폼 데이터 저장"""
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="form_data")
    dataset = models.CharField(max_length=255, verbose_name="데이터셋 코드")
    field_key = models.CharField(max_length=255, verbose_name="필드명")
    field_value = models.TextField(verbose_name="필드값", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('service_request', 'field_key')

    def __str__(self):
        return f"{self.service_request.id} - {self.field_key}: {self.field_value}"


class Dataset(models.Model):
    """데이터셋 정의"""
    name = models.CharField(max_length=255, verbose_name="데이터셋 이름")
    code = models.CharField(max_length=255, unique=True, verbose_name="데이터셋 코드")
    description = models.TextField(blank=True, verbose_name="설명")
    active = models.BooleanField(default=True, verbose_name="활성 여부")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.name} ({self.code})"


class FormElement(models.Model):
    """동적 폼 요소 정의"""
    ELEMENT_TYPES = (
        ('text', '텍스트'),
        ('textarea', '텍스트영역'),
        ('select', '선택박스'),
        ('checkbox', '체크박스'),
        ('radio', '라디오버튼'),
        ('number', '숫자'),
        ('date', '날짜'),
        ('email', '이메일'),
    )
    
    COL_WIDTH_CHOICES = (
        (12, '전체 (12/12)'),
        (6, '절반 (6/12)'),
        (4, '1/3 (4/12)'),
        (3, '1/4 (3/12)'),
    )
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='elements', verbose_name="데이터셋")
    element_name = models.CharField(max_length=255, verbose_name="폼 요소 이름")
    element_code = models.CharField(max_length=255, verbose_name="폼 요소 코드")
    element_type = models.CharField(max_length=20, choices=ELEMENT_TYPES, verbose_name="폼 요소 유형")
    element_options = models.TextField(blank=True, verbose_name="선택 옵션 (JSON)")
    is_required = models.BooleanField(default=False, verbose_name="필수 여부")
    placeholder = models.CharField(max_length=255, blank=True, verbose_name="플레이스홀더")
    order = models.IntegerField(default=0, verbose_name="정렬 순서")
    row_group = models.CharField(max_length=50, blank=True, verbose_name="행 그룹")
    col_width = models.IntegerField(choices=COL_WIDTH_CHOICES, default=12, verbose_name="열 너비")
    active = models.BooleanField(default=True, verbose_name="활성 여부")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dataset', 'order']
        unique_together = ('dataset', 'element_code')

    def __str__(self):
        return f"{self.dataset.name} - {self.element_name}"
