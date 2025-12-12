from django.db import models
from django.contrib.auth.models import User

class System(models.Model):
    """시스템 자산 정보"""
    STATUS_CHOICES = (
        ('DEV', '개발중'),
        ('OPER', '운영중'),
        ('SUSP', '중단'),
        ('DISC', '폐기'),
    )

    name = models.CharField(max_length=100, verbose_name='시스템명')
    code = models.CharField(max_length=50, unique=True, verbose_name='시스템코드')
    description = models.TextField(blank=True, verbose_name='설명')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='담당자', related_name='managed_systems')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPER', verbose_name='상태')
    launch_date = models.DateField(null=True, blank=True, verbose_name='오픈일')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '시스템'
        verbose_name_plural = '시스템 목록'
        ordering = ['name']


class Contract(models.Model):
    """계약 정보 (구축, 유지보수 등)"""
    TYPE_CHOICES = (
        ('BUILD', '구축'),
        ('MAINT', '유지보수'),
        ('LICENSE', '라이선스'),
        ('ETC', '기타'),
    )

    systems = models.ManyToManyField(System, related_name='contracts', verbose_name='관련시스템')
    name = models.CharField(max_length=200, verbose_name='계약명')
    contract_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='계약유형')
    contractor = models.CharField(max_length=100, blank=True, verbose_name='계약업체')
    start_date = models.DateField(verbose_name='계약시작일')
    end_date = models.DateField(verbose_name='계약종료일')
    amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='계약금액')
    content = models.TextField(blank=True, verbose_name='계약내용')
    file = models.FileField(upload_to='contracts/%Y/%m/', null=True, blank=True, verbose_name='계약서 파일')
    related_contracts = models.ManyToManyField('self', blank=True, symmetrical=True, verbose_name='연관계약')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        system_names = ", ".join([s.name for s in self.systems.all()[:2]])
        if self.systems.count() > 2:
            system_names += f" 외 {self.systems.count() - 2}개"
        return f"{self.name} ({system_names})" if system_names else self.name

    class Meta:
        verbose_name = '계약'
        verbose_name_plural = '계약 목록'
        ordering = ['-start_date']


class ContractAttachment(models.Model):
    """계약 첨부파일"""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='attachments', verbose_name='계약')
    file = models.FileField(upload_to='contracts/%Y/%m/', verbose_name='파일')
    filename = models.CharField(max_length=255, verbose_name='파일명')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='업로드자')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드일시')
    description = models.TextField(blank=True, verbose_name='설명')
    
    def __str__(self):
        return f"{self.contract.name} - {self.filename}"
    
    class Meta:
        verbose_name = '계약 첨부파일'
        verbose_name_plural = '계약 첨부파일 목록'
        ordering = ['-uploaded_at']


class Hardware(models.Model):
    """하드웨어 자산 정보"""
    STATUS_CHOICES = (
        ('OPER', '운영중'),
        ('IDLE', '유휴'),
        ('REPAIR', '수리중'),
        ('DISC', '폐기'),
    )

    systems = models.ManyToManyField(System, blank=True, related_name='hardwares', verbose_name='관련시스템')
    name = models.CharField(max_length=100, verbose_name='장비명')
    model_name = models.CharField(max_length=100, blank=True, verbose_name='모델명')
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name='제조사')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='시리얼번호')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='도입일')
    warranty_date = models.DateField(null=True, blank=True, verbose_name='보증만료일')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPER', verbose_name='상태')
    specifications = models.TextField(blank=True, verbose_name='상세사양')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.model_name})"

    class Meta:
        verbose_name = '하드웨어'
        verbose_name_plural = '하드웨어 목록'
        ordering = ['name']


class Software(models.Model):
    """소프트웨어 자산 정보"""
    STATUS_CHOICES = (
        ('OPER', '운영중'),
        ('EXP', '만료'),
        ('DISC', '폐기'),
    )
    LICENSE_TYPE_CHOICES = (
        ('PERP', '영구'),
        ('SUB', '구독'),
        ('OPEN', '오픈소스'),
    )

    systems = models.ManyToManyField(System, blank=True, related_name='softwares', verbose_name='관련시스템')
    name = models.CharField(max_length=100, verbose_name='소프트웨어명')
    version = models.CharField(max_length=50, blank=True, verbose_name='버전')
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name='제조사')
    license_type = models.CharField(max_length=10, choices=LICENSE_TYPE_CHOICES, default='PERP', verbose_name='라이선스 유형')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='도입일')
    warranty_date = models.DateField(null=True, blank=True, verbose_name='유지보수만료일')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPER', verbose_name='상태')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} {self.version}"

    class Meta:
        verbose_name = '소프트웨어'
        verbose_name_plural = '소프트웨어 목록'
        ordering = ['name']


class AssetHistory(models.Model):
    """통합 자산 변경 이력"""
    
    ASSET_TYPE_CHOICES = (
        ('SYSTEM', '시스템'),
        ('CONTRACT', '계약'),
        ('HARDWARE', '하드웨어'),
        ('SOFTWARE', '소프트웨어'),
    )
    
    ACTION_CHOICES = (
        ('CREATE', '생성'),
        ('UPDATE', '수정'),
        ('CONTRACT_ADD', '계약 연결'),
        ('CONTRACT_REMOVE', '계약 해제'),
        ('HARDWARE_ADD', '하드웨어 연결'),
        ('HARDWARE_REMOVE', '하드웨어 해제'),
        ('SOFTWARE_ADD', '소프트웨어 연결'),
        ('SOFTWARE_REMOVE', '소프트웨어 해제'),
        ('SYSTEM_ADD', '시스템 연결'),
        ('SYSTEM_REMOVE', '시스템 해제'),
        ('LINK_CONTRACT_ADD', '연관계약 연결'),
        ('LINK_CONTRACT_REMOVE', '연관계약 해제'),
        ('USER_COMMENT', '사용자 입력'),
        ('REGULAR_INSPECTION', '정기점검'),
    )
    
    # Asset type and reference
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES, verbose_name='자산 유형')
    
    # Foreign keys to each asset type (only one will be set)
    system = models.ForeignKey(System, on_delete=models.CASCADE, null=True, blank=True, related_name='histories', verbose_name='시스템')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True, related_name='histories', verbose_name='계약')
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, null=True, blank=True, related_name='histories', verbose_name='하드웨어')
    software = models.ForeignKey(Software, on_delete=models.CASCADE, null=True, blank=True, related_name='histories', verbose_name='소프트웨어')
    
    # Common fields
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='작업')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='작업자')
    comment = models.TextField(blank=True, verbose_name='코멘트')
    
    # Related objects (optional, for relationship changes)
    related_system = models.ForeignKey(System, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_histories', verbose_name='관련 시스템')
    related_contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_histories', verbose_name='관련 계약')
    related_hardware = models.ForeignKey(Hardware, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_histories', verbose_name='관련 하드웨어')
    related_software = models.ForeignKey(Software, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_histories', verbose_name='관련 소프트웨어')
    
    # Changed data (JSON)
    changed_fields = models.JSONField(null=True, blank=True, verbose_name='변경 필드')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='기록일시')
    
    def get_asset(self):
        """Return the actual asset object"""
        if self.asset_type == 'SYSTEM':
            return self.system
        elif self.asset_type == 'CONTRACT':
            return self.contract
        elif self.asset_type == 'HARDWARE':
            return self.hardware
        elif self.asset_type == 'SOFTWARE':
            return self.software
        return None
    
    def get_asset_name(self):
        """Return the name of the asset"""
        asset = self.get_asset()
        return asset.name if asset else ''
    
    def __str__(self):
        asset_name = self.get_asset_name()
        return f"[{self.get_asset_type_display()}] {asset_name} - {self.get_action_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    class Meta:
        verbose_name = '자산 이력'
        verbose_name_plural = '자산 이력 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_type', '-created_at']),
            models.Index(fields=['system', '-created_at']),
            models.Index(fields=['contract', '-created_at']),
            models.Index(fields=['hardware', '-created_at']),
            models.Index(fields=['software', '-created_at']),
        ]





class RegularInspection(models.Model):
    """정기점검 계획 및 결과"""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='inspections', verbose_name='계약')
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='inspections', verbose_name='시스템')
    inspection_date = models.DateField(verbose_name='점검일자')
    inspection_month = models.CharField(max_length=7, verbose_name='점검월', help_text='YYYY-MM 형식')
    result = models.TextField(verbose_name='점검결과')
    file = models.FileField(upload_to='inspections/%Y/%m/', null=True, blank=True, verbose_name='첨부파일')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    def __str__(self):
        return f"[{self.inspection_month}] {self.system.name} 정기점검"

    class Meta:
        verbose_name = '정기점검'
        verbose_name_plural = '정기점검 목록'
        ordering = ['-inspection_date', '-created_at']


class RegularInspectionAttachment(models.Model):
    """정기점검 첨부파일"""
    inspection = models.ForeignKey(RegularInspection, on_delete=models.CASCADE, related_name='attachments', verbose_name='정기점검')
    file = models.FileField(upload_to='inspections/%Y/%m/', verbose_name='파일')
    filename = models.CharField(max_length=255, verbose_name='파일명')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드일시')
    
    def __str__(self):
        return f"{self.inspection} - {self.filename}"
    
    class Meta:
        verbose_name = '정기점검 첨부파일'
        verbose_name_plural = '정기점검 첨부파일 목록'
        ordering = ['-uploaded_at']


