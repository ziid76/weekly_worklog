# 운행일지 입력은 헤더에 별도 메타 폼이 없고 14일 항목은 AJAX 로 저장하므로
# Django Form 을 사용하지 않는다.

from django import forms

from .models import Executive


class ExecutiveForm(forms.ModelForm):
    """수행임원 마스터 CRUD 폼 (지원팀 관리자용).

    입력: 이름 / 수신 이메일 / 활성화 여부 / 표시 순서.
    """

    # 공통 Tailwind 입력 스타일 (admin_sheet_list.html 의 둥근 인풋과 통일)
    _input_cls = (
        'w-full rounded-full border border-slate-200 px-4 py-2.5 text-sm '
        'focus:ring-2 focus:ring-primary/40 focus:border-primary'
    )

    class Meta:
        model = Executive
        fields = ['name', 'email', 'is_active', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': '예) 홍길동 전무',
                'maxlength': 50,
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': '예) executive@samchully.co.kr',
            }),
            'display_order': forms.NumberInput(attrs={
                'min': 0,
                'step': 1,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 accent-primary',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 체크박스를 제외한 입력 위젯에 공통 스타일 부여
        for name, field in self.fields.items():
            if name == 'is_active':
                continue
            field.widget.attrs.setdefault('class', self._input_cls)

    def clean_name(self):
        return (self.cleaned_data.get('name') or '').strip()
