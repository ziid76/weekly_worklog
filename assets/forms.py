from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import System, Contract, Hardware, Software, ContractAttachment, RegularInspection


class SystemForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        queryset=User.objects.all().select_related('profile'),
        required=False,
        label='담당자',
        empty_label='담당자를 선택하세요'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # manager 필드의 선택지를 profile의 display_name으로 표시
        self.fields['manager'].label_from_instance = lambda obj: obj.profile.display_name
        
        # 수정 시에는 시스템구분을 변경하지 못하도록 하거나, 코드가 이미 있으면 코드 필드를 읽기 전용으로 설정
        if self.instance.pk:
            self.fields['code'].widget.attrs['readonly'] = True
            # 이미 코드가 있으면 구분도 변경하지 못하게 하는 것이 안전함 (채번 규칙 상)
            self.fields['system_type'].disabled = True
        else:
            # 신규 등록 시 코드는 자동 생성되므로 입력 필수 해제 (blank=True 되어있음)
            self.fields['code'].required = False
            self.fields['code'].widget.attrs['placeholder'] = '자동 생성됩니다'
            self.fields['code'].widget.attrs['readonly'] = True
    
    class Meta:
        model = System
        fields = ['system_type', 'name', 'code', 'description', 'manager', 'status', 'launch_date']
        widgets = {
            'system_type': forms.RadioSelect(),
            'launch_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ContractForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        queryset=User.objects.all().select_related('profile'),
        required=False,
        label='담당자',
        empty_label='담당자를 선택하세요'
    )

    class Meta:
        model = Contract
        fields = ['systems', 'name', 'contract_type', 'contractor', 'manager', 'start_date', 'end_date', 'amount', 'content', 'is_regular_inspection', 'inspection_schedule']
        input_class = 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 focus:border-primary focus:ring-1 focus:ring-primary transition-all placeholder:text-slate-400 outline-none'
        
        widgets = {
            'systems': forms.SelectMultiple(attrs={'style': 'display:none;'}),
            'name': forms.TextInput(attrs={'class': input_class}),
            'contract_type': forms.Select(attrs={'class': input_class}),
            'contractor': forms.TextInput(attrs={'class': input_class}),
            'manager': forms.Select(attrs={'class': input_class}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': input_class}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': input_class}),
            'amount': forms.NumberInput(attrs={'class': input_class}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': input_class}),
            'is_regular_inspection': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-primary focus:ring-primary'}),
            'inspection_schedule': forms.HiddenInput(),
        }

    inspection_schedule_months = forms.MultipleChoiceField(
        choices=[(str(i), f"{i}월") for i in range(1, 13)],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'flex flex-wrap gap-4'}),
        required=False,
        label='정기점검 스케줄'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # manager 필드의 선택지를 profile의 display_name으로 표시
        self.fields['manager'].label_from_instance = lambda obj: obj.profile.display_name if hasattr(obj, 'profile') and obj.profile.display_name else obj.username
        
        self.fields['systems'].error_messages['required'] = '계약과 관련된 시스템을 최소 하나 이상 선택해야 합니다.'
        if self.instance and self.instance.pk:
            schedule = self.instance.inspection_schedule
            if schedule:
                self.fields['inspection_schedule_months'].initial = [str(m) for m in schedule]

    def clean(self):
        cleaned_data = super().clean()
        months = cleaned_data.get('inspection_schedule_months')
        if months:
            cleaned_data['inspection_schedule'] = [int(m) for m in months]
        else:
            cleaned_data['inspection_schedule'] = []
        
        # is_regular_inspection이 거짓이면 스케줄 비우기
        if not cleaned_data.get('is_regular_inspection'):
            cleaned_data['inspection_schedule'] = []
        
        # 정기점검 대상인데 시스템이 없는 경우 추가 검증
        if cleaned_data.get('is_regular_inspection') and not cleaned_data.get('systems'):
            self.add_error('systems', '정기점검 대상 계약은 반드시 하나 이상의 시스템이 연결되어야 합니다.')
            
        return cleaned_data

class HardwareForm(forms.ModelForm):
    class Meta:
        model = Hardware
        fields = ['systems', 'name', 'model_name', 'manufacturer', 'serial_number', 'purchase_date', 'warranty_date', 'status', 'specifications']
        widgets = {
            'systems': forms.CheckboxSelectMultiple(),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_date': forms.DateInput(attrs={'type': 'date'}),
            'specifications': forms.Textarea(attrs={'rows': 4}),
        }

class SoftwareForm(forms.ModelForm):
    class Meta:
        model = Software
        fields = ['systems', 'name', 'version', 'manufacturer', 'license_type', 'purchase_date', 'warranty_date', 'status']
        widgets = {
            'systems': forms.CheckboxSelectMultiple(),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_date': forms.DateInput(attrs={'type': 'date'}),
        }

class RegularInspectionForm(forms.ModelForm):
    class Meta:
        model = RegularInspection
        fields = ['contract', 'system', 'inspection_month', 'inspection_date', 'result', 'file']
        input_class = 'w-full bg-slate-50 border border-slate-200 rounded-md px-4 py-2 focus:border-primary focus:ring-1 focus:ring-primary transition-all placeholder:text-slate-400'
        
        widgets = {
            'contract': forms.Select(attrs={'class': input_class}),
            'system': forms.Select(attrs={'class': input_class}),
            'inspection_month': forms.TextInput(attrs={'type': 'month', 'class': input_class}),
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': input_class}),
            'result': forms.Textarea(attrs={'rows': 3, 'class': input_class, 'style': 'height: auto !important;'}),
            'file': forms.ClearableFileInput(attrs={'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-slate-900 focus:border-primary focus:ring-1 focus:ring-primary transition-all placeholder:text-slate-400'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            today = timezone.now().date()
            if 'inspection_month' in self.fields:
                self.fields['inspection_month'].initial = today.strftime('%Y-%m')
            if 'inspection_date' in self.fields:
                self.fields['inspection_date'].initial = today

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='엑셀 파일 선택')
