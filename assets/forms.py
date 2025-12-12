from django import forms
from django.contrib.auth.models import User
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
    
    class Meta:
        model = System
        fields = ['name', 'code', 'description', 'manager', 'status', 'launch_date']
        widgets = {
            'launch_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['systems', 'name', 'contract_type', 'contractor', 'start_date', 'end_date', 'amount', 'content']
        widgets = {
            'systems': forms.SelectMultiple(attrs={'style': 'display:none;'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'content': forms.Textarea(attrs={'rows': 4}),
        }

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
        widgets = {
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'system': forms.Select(attrs={'class': 'form-select'}),
            'inspection_month': forms.TextInput(attrs={'type': 'month', 'class': 'form-control'}),
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'result': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }
