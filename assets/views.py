from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.core.paginator import Paginator
from .models import System, Contract, Hardware, Software, AssetHistory, ContractAttachment, SystemAttachment, RegularInspection, RegularInspectionAttachment
from .forms import SystemForm, ContractForm, HardwareForm, SoftwareForm, RegularInspectionForm, ExcelUploadForm
from .history_utils import create_asset_history
import os
import pandas as pd
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Value
from django.db.models.functions import Concat
from accounts.models import UserProfile

class SystemListView(LoginRequiredMixin, ListView):
    model = System
    template_name = 'assets/system_list.html'
    context_object_name = 'systems'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        # 상태 필터 가져오기 (getlist 사용)
        status_filter = self.request.GET.getlist('status')
        my_system = self.request.GET.get('my_system') == 'true'
        
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q)
            )
            
        # 빈 문자열 제외 (전체 옵션 대응)
        status_filter = [s for s in status_filter if s]
        
        # 첫 진입 시(파라미터가 없을 때) 기본값 OPER 설정
        # 단, q나 my_system 검색 시에는 명시적으로 선택하지 않은 이상 필터를 걸지 않거나 
        # 사용자 편의를 위해 첫 로드 시에만 적용함.
        # 여기서는 request.GET에 'status' 자체가 없을 때 OPER를 기본으로 함.
        if not self.request.GET.get('status') and not q and not my_system:
            status_filter = ['OPER']

        if status_filter:
            queryset = queryset.filter(status__in=status_filter)

        if my_system:
            queryset = queryset.filter(manager=self.request.user)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_system'] = self.request.GET.get('my_system') == 'true'
        # 현재 선택된 상태 리스트 (빈 값 제외)
        context['current_statuses'] = [s for s in self.request.GET.getlist('status') if s]
        # 첫 진입 시(파라미터가 없을 때) 기본값 반영
        if not self.request.GET.get('status') and not self.request.GET.get('q') and not context['my_system']:
            context['current_statuses'] = ['OPER']
        return context

class SystemDetailView(LoginRequiredMixin, DetailView):
    model = System
    template_name = 'assets/system_detail.html'
    context_object_name = 'system'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hardwares'] = self.object.hardwares.all()
        context['softwares'] = self.object.softwares.all()
        context['attachments'] = self.object.attachments.all()
        context['histories'] = self.object.histories.all()[:20]  # 최근 20개
        context['inspections'] = self.object.inspections.all()
        context['inspection_form'] = RegularInspectionForm(initial={'system': self.object})
        # Hide system field and filter contracts
        from django import forms
        context['inspection_form'].fields['system'].widget = forms.HiddenInput()
        context['inspection_form'].fields['contract'].queryset = self.object.contracts.all()
        return context

class SystemCreateView(LoginRequiredMixin, CreateView):
    model = System
    form_class = SystemForm
    template_name = 'assets/system_form.html'
    success_url = reverse_lazy('assets:system_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        files = self.request.FILES.getlist('attachments')
        for file in files:
            SystemAttachment.objects.create(
                system=self.object,
                file=file,
                filename=file.name,
                uploaded_by=self.request.user
            )
        return response

class SystemUpdateView(LoginRequiredMixin, UpdateView):
    model = System
    form_class = SystemForm
    template_name = 'assets/system_form.html'
    
    def get_success_url(self):
        return reverse_lazy('assets:system_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        files = self.request.FILES.getlist('attachments')
        for file in files:
            SystemAttachment.objects.create(
                system=self.object,
                file=file,
                filename=file.name,
                uploaded_by=self.request.user
            )
        return response

class SystemBulkUpdateView(LoginRequiredMixin, View):
    """Excel 기반 시스템 일괄 업데이트"""
    def post(self, request):
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file)
                
                # 필수 컬럼 확인
                required_cols = ['시스템명']
                if not all(col in df.columns for col in required_cols):
                    messages.error(request, f"필수 컬럼이 누락되었습니다: {required_cols}")
                    return redirect('assets:system_list')

                updated_count = 0
                created_count = 0
                errors = []

                for index, row in df.iterrows():
                    code = str(row.get('시스템코드', '')).strip()
                    if code == 'nan': code = ''
                    
                    name = str(row['시스템명']).strip()
                    desc = str(row.get('설명', '')).strip()
                    status_name = str(row.get('상태', '운영중')).strip()
                    manager_name = str(row.get('담당자', '')).strip()
                    type_name = str(row.get('구분', '일반')).strip()
                    
                    # 상태 매핑
                    status_map = {'개발중': 'DEV', '운영중': 'OPER', '중단': 'SUSP', '폐기': 'DISC'}
                    status = status_map.get(status_name, 'OPER')

                    # 구분 매핑
                    type_map = {'일반': 'SAM', '보안': 'SEC', 'SAM': 'SAM', 'SEC': 'SEC'}
                    system_type = type_map.get(type_name, 'SAM')

                    # 담당자 찾기
                    manager = None
                    if manager_name and manager_name not in ['nan', 'None']:
                        # 1. username 검색
                        manager = User.objects.filter(username=manager_name).first()
                        
                        # 2. 한국어 이름 검색 (UserProfile 활용)
                        if not manager:
                            profile = UserProfile.objects.annotate(
                                full_name=Concat('last_name_ko', 'first_name_ko')
                            ).filter(full_name=manager_name).first()
                            
                            if not profile:
                                profile = UserProfile.objects.annotate(
                                    full_name=Concat('user__last_name', 'user__first_name')
                                ).filter(full_name=manager_name).first()
                            
                            if profile:
                                manager = profile.user

                    try:
                        if code:
                            system, created = System.objects.update_or_create(
                                code=code,
                                defaults={
                                    'name': name,
                                    'system_type': system_type,
                                    'description': desc,
                                    'status': status,
                                    'manager': manager,
                                }
                            )
                        else:
                            # 코드가 없으면 신규 생성 (save()에서 자동 채번)
                            system = System.objects.create(
                                name=name,
                                system_type=system_type,
                                description=desc,
                                status=status,
                                manager=manager,
                            )
                            created = True
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
                        # 이력 남기기
                        create_asset_history(
                            asset_type='SYSTEM',
                            asset=system,
                            action='CREATE' if created else 'UPDATE',
                            user=request.user,
                            comment=f"엑셀 일괄 {'등록' if created else '수정'}"
                        )
                    except Exception as e:
                        errors.append(f"Row {index+2} ({code}): {str(e)}")

                msg = f"일괄 업데이트 완료: 신규 {created_count}건, 수정 {updated_count}건"
                if errors:
                    msg += f" (에러 {len(errors)}건)"
                    messages.warning(request, msg)
                    for err in errors[:5]: # 최대 5개만 표시
                        messages.error(request, err)
                else:
                    messages.success(request, msg)

            except Exception as e:
                messages.error(request, f"파일 처리 중 오류 발생: {str(e)}")
        else:
            messages.error(request, "유효하지 않은 파일 형식입니다.")
            
        return redirect('assets:system_list')

class SystemExportView(LoginRequiredMixin, View):
    """시스템 목록 Excel 다운로드"""
    def get(self, request):
        # 현재 필터 조건 적용
        queryset = System.objects.all().select_related('manager', 'manager__profile')
        q = request.GET.get('q')
        my_system = request.GET.get('my_system') == 'true'
        
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q)
            )
        if my_system:
            queryset = queryset.filter(manager=request.user)
            
        # 데이터 프레임 생성용 리스트
        data = []
        status_map_rev = {'DEV': '개발중', 'OPER': '운영중', 'SUSP': '중단', 'DISC': '폐기'}
        type_map_rev = {'SAM': '일반', 'SEC': '보안'}
        
        for sys in queryset:
            manager_display = ""
            if sys.manager:
                manager_display = sys.manager.profile.display_name if hasattr(sys.manager, 'profile') else sys.manager.username
                
            data.append({
                '시스템명': sys.name,
                '시스템코드': sys.code,
                '구분': type_map_rev.get(sys.system_type, '일반'),
                '설명': sys.description,
                '담당자': manager_display,
                '상태': status_map_rev.get(sys.status, '운영중'),
            })
            
        df = pd.DataFrame(data)
        
        # Excel 파일 생성
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Systems')
            
        output.seek(0)
        
        from django.utils import timezone
        filename = f"ITMS_Systems_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

class RegularInspectionDashboardView(LoginRequiredMixin, ListView):
    """정기점검 관리 대시보드"""
    model = Contract
    template_name = 'assets/inspection_dashboard.html'
    context_object_name = 'contracts'

    def get_queryset(self):
        return Contract.objects.filter(is_regular_inspection=True).prefetch_related('systems', 'inspections')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import datetime
        today = datetime.date.today()
        year = int(self.request.GET.get('year', today.year))
        
        contracts = self.get_queryset()
        
        # 년도 범위 (현재 기준 전후 2년)
        context['year_range'] = range(today.year - 2, today.year + 3)
        context['selected_year'] = year
        
        # 대시보드 데이터 구성
        dashboard_data = []
        for contract in contracts:
            months_data = []
            for m in range(1, 13):
                is_planned = m in (contract.inspection_schedule or [])
                
                # 해당 월의 점검 내역 확인 (YYYY-MM 형식 매칭)
                month_str = f"{year}-{m:02d}"
                actual_inspections = contract.inspections.filter(inspection_month=month_str)
                
                # 시스템별 점검 현황 (계약에 속한 모든 시스템이 점검되었는지 확인)
                total_systems = contract.systems.count()
                inspected_systems_count = actual_inspections.values('system').distinct().count()
                
                is_done = inspected_systems_count > 0
                is_all_done = total_systems > 0 and inspected_systems_count >= total_systems
                
                months_data.append({
                    'month': m,
                    'is_planned': is_planned,
                    'is_done': is_done,
                    'is_all_done': is_all_done,
                    'inspections': actual_inspections,
                    'inspected_count': inspected_systems_count,
                    'total_count': total_systems,
                })
            
            dashboard_data.append({
                'contract': contract,
                'months': months_data,
            })
            
        context['dashboard_data'] = dashboard_data
        return context

class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'assets/contract_list.html'
    context_object_name = 'contracts'
    ordering = ['-start_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        year = self.request.GET.get('year')
        my_contract = self.request.GET.get('my_contract') == 'true'
        
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(contractor__icontains=q) | Q(systems__name__icontains=q)
            )
        
        if year:
            # 계약기간이 해당 연도에 포함되는 경우 필터링
            # start_date가 해당 연도 이전이고, end_date가 해당 연도 이후인 경우
            queryset = queryset.filter(
                start_date__year__lte=year,
                end_date__year__gte=year
            )
        
        if my_contract:
            queryset = queryset.filter(Q(manager=self.request.user) | Q(systems__manager=self.request.user))
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 계약이 실제로 존재하는 연도만 제공
        from django.db.models import Q
        
        # 모든 계약의 연도 범위를 수집
        contracts = Contract.objects.all()
        years_set = set()
        
        for contract in contracts:
            # 계약 기간에 포함되는 모든 연도 추가
            start_year = contract.start_date.year
            end_year = contract.end_date.year
            for year in range(start_year, end_year + 1):
                years_set.add(year)
        
        # 정렬된 리스트로 변환 (내림차순)
        context['year_range'] = sorted(list(years_set), reverse=True)
        context['my_contract'] = self.request.GET.get('my_contract') == 'true'
        return context

class ContractCreateView(LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'assets/contract_form.html'
    success_url = reverse_lazy('assets:contract_list')

    def get_initial(self):
        initial = super().get_initial()
        system_id = self.request.GET.get('system')
        if system_id:
            initial['system'] = system_id
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle multiple file uploads
        files = self.request.FILES.getlist('attachments')
        for file in files:
            ContractAttachment.objects.create(
                contract=self.object,
                file=file,
                filename=file.name,
                uploaded_by=self.request.user
            )
        return response

class ContractUpdateView(LoginRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'assets/contract_form.html'
    
    def get_success_url(self):
        return reverse_lazy('assets:contract_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle multiple file uploads
        files = self.request.FILES.getlist('attachments')
        for file in files:
            ContractAttachment.objects.create(
                contract=self.object,
                file=file,
                filename=file.name,
                uploaded_by=self.request.user
            )
        return response

class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'assets/contract_detail.html'
    context_object_name = 'contract'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['histories'] = self.object.histories.all()[:20]
        context['attachments'] = self.object.attachments.all()
        context['inspections'] = self.object.inspections.all()
        context['inspection_form'] = RegularInspectionForm(initial={'contract': self.object})
        # Hide contract field and filter systems
        from django import forms
        context['inspection_form'].fields['contract'].widget = forms.HiddenInput()
        context['inspection_form'].fields['system'].queryset = self.object.systems.all()
        return context


class HardwareListView(LoginRequiredMixin, ListView):
    model = Hardware
    template_name = 'assets/hardware_list.html'
    context_object_name = 'hardwares'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(model_name__icontains=q) | Q(systems__name__icontains=q)
            ).distinct()
        return queryset

class HardwareCreateView(LoginRequiredMixin, CreateView):
    model = Hardware
    form_class = HardwareForm
    template_name = 'assets/hardware_form.html'
    success_url = reverse_lazy('assets:hardware_list')

    def get_initial(self):
        initial = super().get_initial()
        system_id = self.request.GET.get('system')
        if system_id:
            initial['system'] = system_id
        return initial

class HardwareUpdateView(LoginRequiredMixin, UpdateView):
    model = Hardware
    form_class = HardwareForm
    template_name = 'assets/hardware_form.html'
    
    def get_success_url(self):
        return reverse_lazy('assets:hardware_detail', kwargs={'pk': self.object.pk})

class HardwareDetailView(LoginRequiredMixin, DetailView):
    model = Hardware
    template_name = 'assets/hardware_detail.html'
    context_object_name = 'hardware'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['histories'] = self.object.histories.all()[:20]
        # 해당 하드웨어가 속한 시스템들의 계약 정보 가져오기
        context['contracts'] = Contract.objects.filter(systems__in=self.object.systems.all()).distinct()
        return context


class SoftwareListView(LoginRequiredMixin, ListView):
    model = Software
    template_name = 'assets/software_list.html'
    context_object_name = 'softwares'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(version__icontains=q) | Q(systems__name__icontains=q)
            ).distinct()
        return queryset

class SoftwareCreateView(LoginRequiredMixin, CreateView):
    model = Software
    form_class = SoftwareForm
    template_name = 'assets/software_form.html'
    success_url = reverse_lazy('assets:software_list')

    def get_initial(self):
        initial = super().get_initial()
        system_id = self.request.GET.get('system')
        if system_id:
            initial['system'] = system_id
        return initial

class SoftwareUpdateView(LoginRequiredMixin, UpdateView):
    model = Software
    form_class = SoftwareForm
    template_name = 'assets/software_form.html'
    
    def get_success_url(self):
        return reverse_lazy('assets:software_detail', kwargs={'pk': self.object.pk})

class SoftwareDetailView(LoginRequiredMixin, DetailView):
    model = Software
    template_name = 'assets/software_detail.html'
    context_object_name = 'software'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['histories'] = self.object.histories.all()[:20]
        # 해당 소프트웨어가 속한 시스템들의 계약 정보 가져오기
        context['contracts'] = Contract.objects.filter(systems__in=self.object.systems.all()).distinct()
        return context


# Related Contracts API Views
class ContractSearchView(LoginRequiredMixin, View):
    """Search contracts for adding as related contracts"""
    def get(self, request, pk):
        q = request.GET.get('q', '').strip()
        current_contract = get_object_or_404(Contract, pk=pk)
        
        # Start with all contracts excluding the current one
        contracts = Contract.objects.exclude(pk=pk)
        
        # Exclude already related contracts
        related_ids = current_contract.related_contracts.values_list('id', flat=True)
        contracts = contracts.exclude(id__in=related_ids)
        
        # Apply search filter if query provided
        if q:
            contracts = contracts.filter(
                Q(name__icontains=q) | Q(contractor__icontains=q) | Q(systems__name__icontains=q)
            )
        
        # Limit to 20 results
        contracts = contracts.prefetch_related('systems')[:20]
        
        data = [{
            'id': c.id,
            'name': c.name,
            'contractor': c.contractor,
            'system_names': ', '.join([s.name for s in c.systems.all()]),
            'start_date': c.start_date.strftime('%Y-%m-%d'),
            'end_date': c.end_date.strftime('%Y-%m-%d'),
        } for c in contracts]
        
        return JsonResponse({'contracts': data})


class AddRelatedContractView(LoginRequiredMixin, View):
    """Add a related contract"""
    def post(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        related_id = request.POST.get('related_id')
        
        if not related_id:
            return JsonResponse({'success': False, 'error': '관련 계약 ID가 필요합니다.'})
        
        try:
            related_contract = Contract.objects.get(pk=related_id)
            contract.related_contracts.add(related_contract)
            return JsonResponse({
                'success': True,
                'contract': {
                    'id': related_contract.id,
                    'name': related_contract.name,
                    'contractor': related_contract.contractor,
                    'system_names': ', '.join([s.name for s in related_contract.systems.all()]),
                    'start_date': related_contract.start_date.strftime('%Y-%m-%d'),
                    'end_date': related_contract.end_date.strftime('%Y-%m-%d'),
                }
            })
        except Contract.DoesNotExist:
            return JsonResponse({'success': False, 'error': '계약을 찾을 수 없습니다.'})


class RemoveRelatedContractView(LoginRequiredMixin, View):
    """Remove a related contract"""
    def post(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        related_id = request.POST.get('related_id')
        
        if not related_id:
            return JsonResponse({'success': False, 'error': '관련 계약 ID가 필요합니다.'})
        
        try:
            related_contract = Contract.objects.get(pk=related_id)
            contract.related_contracts.remove(related_contract)
            return JsonResponse({'success': True})
        except Contract.DoesNotExist:
            return JsonResponse({'success': False, 'error': '계약을 찾을 수 없습니다.'})


# Contract-System AJAX Views
class ContractSystemSearchView(LoginRequiredMixin, View):
    """Search systems for adding to a contract (excluding those already linked)"""
    def get(self, request, pk):
        q = request.GET.get('q', '').strip()
        contract = get_object_or_404(Contract, pk=pk)
        
        # Start with all systems
        systems = System.objects.all()
        
        # Exclude systems already linked to this contract
        linked_ids = contract.systems.values_list('id', flat=True)
        systems = systems.exclude(id__in=linked_ids)
        
        # Apply search filter if query provided
        if q:
            systems = systems.filter(
                Q(name__icontains=q) | 
                Q(code__icontains=q) | 
                Q(description__icontains=q)
            )
        
        # Order and limit
        systems = systems.select_related('manager__profile').order_by('name')[:20]
        
        data = [{
            'id': s.id,
            'name': s.name,
            'code': s.code,
            'manager_name': s.manager.profile.display_name if hasattr(s.manager, 'profile') else s.manager.username if s.manager else '-',
            'status': s.get_status_display(),
            'status_code': s.status,
        } for s in systems]
        
        return JsonResponse({'systems': data})


class AddContractSystemView(LoginRequiredMixin, View):
    """Add a system to a contract via AJAX"""
    def post(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        system_id = request.POST.get('system_id')
        
        if not system_id:
            return JsonResponse({'success': False, 'error': '시스템 ID가 필요합니다.'})
        
        try:
            system = System.objects.get(pk=system_id)
            contract.systems.add(system)
            
            # Add history
            create_asset_history(
                asset_type='CONTRACT',
                asset=contract,
                action='SYSTEM_ADD',
                user=request.user,
                comment=f'시스템 연결: {system.name}',
                related_system=system
            )
            
            return JsonResponse({
                'success': True,
                'system': {
                    'id': system.id,
                    'name': system.name,
                    'code': system.code
                }
            })
        except System.DoesNotExist:
            return JsonResponse({'success': False, 'error': '시스템을 찾을 수 없습니다.'})


class RemoveContractSystemView(LoginRequiredMixin, View):
    """Remove a system from a contract via AJAX"""
    def post(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        system_id = request.POST.get('system_id')
        
        if not system_id:
            return JsonResponse({'success': False, 'error': '시스템 ID가 필요합니다.'})
        
        try:
            system = System.objects.get(pk=system_id)
            contract.systems.remove(system)
            
            # Add history
            create_asset_history(
                asset_type='CONTRACT',
                asset=contract,
                action='SYSTEM_REMOVE',
                user=request.user,
                comment=f'시스템 해제: {system.name}',
                related_system=system
            )
            
            return JsonResponse({'success': True})
        except System.DoesNotExist:
            return JsonResponse({'success': False, 'error': '시스템을 찾을 수 없습니다.'})


class SystemSearchView(LoginRequiredMixin, View):
    """Search systems with pagination for form selection"""
    def get(self, request):
        q = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Get all systems
        systems = System.objects.select_related('manager__profile').all()
        
        # Apply search filter if query provided
        if q:
            systems = systems.filter(
                Q(name__icontains=q) | 
                Q(code__icontains=q) | 
                Q(description__icontains=q)
            )
        
        # Order by name
        systems = systems.order_by('name')
        
        # Paginate
        paginator = Paginator(systems, page_size)
        page_obj = paginator.get_page(page)
        
        # Prepare data
        data = {
            'systems': [{
                'id': s.id,
                'name': s.name,
                'code': s.code,
                'manager_name': s.manager.profile.display_name if hasattr(s.manager, 'profile') else s.manager.username,
                'status': s.get_status_display(),
                'status_code': s.status,
            } for s in page_obj],
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            }
        }
        
        return JsonResponse(data)


class SystemHistoryCreateView(LoginRequiredMixin, View):
    """시스템 이력 추가"""
    def post(self, request, pk):
        system = get_object_or_404(System, pk=pk)
        comment = request.POST.get('comment', '')
        action = request.POST.get('action', 'USER_COMMENT')
        
        if comment:
            create_asset_history(
                asset_type='SYSTEM',
                asset=system,
                action=action,
                user=request.user,
                comment=comment
            )
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': '코멘트를 입력해주세요.'})

class ContractHistoryCreateView(LoginRequiredMixin, View):
    """계약 이력 추가"""
    def post(self, request, pk):

        contract = get_object_or_404(Contract, pk=pk)
        comment = request.POST.get('comment', '')
        action = request.POST.get('action', 'USER_COMMENT')
        if comment:
            create_asset_history(
                asset_type='CONTRACT',
                asset=contract,
                action=action,
                user=request.user,
                comment=comment
            )
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': '코멘트를 입력해주세요.'})

class HardwareHistoryCreateView(LoginRequiredMixin, View):
    """하드웨어 이력 추가"""
    def post(self, request, pk):
        hardware = get_object_or_404(Hardware, pk=pk)
        comment = request.POST.get('comment', '')
        action = request.POST.get('action', 'USER_COMMENT')
        if comment:
            create_asset_history(
                asset_type='HARDWARE',
                asset=hardware,
                action=action,
                user=request.user,
                comment=comment
            )
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': '코멘트를 입력해주세요.'})

class SoftwareHistoryCreateView(LoginRequiredMixin, View):
    """소프트웨어 이력 추가"""
    def post(self, request, pk):
        software = get_object_or_404(Software, pk=pk)
        comment = request.POST.get('comment', '')
        action = request.POST.get('action', 'USER_COMMENT')
        
        if comment:
            create_asset_history(
                asset_type='SOFTWARE',
                asset=software,
                action=action,
                user=request.user,
                comment=comment
            )
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': '코멘트를 입력해주세요.'})


class ContractAttachmentDeleteView(LoginRequiredMixin, View):
    """계약 첨부파일 삭제"""
    def post(self, request, pk, attachment_id):
        contract = get_object_or_404(Contract, pk=pk)
        attachment = get_object_or_404(ContractAttachment, pk=attachment_id, contract=contract)
        
        # Delete the file from storage
        if attachment.file:
            if os.path.isfile(attachment.file.path):
                os.remove(attachment.file.path)
        
        # Delete the database record
        attachment.delete()
        
        return JsonResponse({'success': True})


class SystemAttachmentDeleteView(LoginRequiredMixin, View):
    """시스템 첨부파일 삭제"""
    def post(self, request, pk, attachment_id):
        system = get_object_or_404(System, pk=pk)
        attachment = get_object_or_404(SystemAttachment, pk=attachment_id, system=system)

        # Delete the file from storage
        if attachment.file:
            if os.path.isfile(attachment.file.path):
                os.remove(attachment.file.path)

        # Delete the database record
        attachment.delete()

        return JsonResponse({'success': True})


class RegularInspectionCreateView(LoginRequiredMixin, CreateView):
    """정기점검 등록"""
    model = RegularInspection
    form_class = RegularInspectionForm
    template_name = 'assets/inspection_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        system_id = self.request.GET.get('system')
        contract_id = self.request.GET.get('contract')
        if system_id:
            initial['system'] = system_id
        if contract_id:
            initial['contract'] = contract_id
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Handle multiple file uploads
        files = self.request.FILES.getlist('attachments')
        for file in files:
            RegularInspectionAttachment.objects.create(
                inspection=self.object,
                file=file,
                filename=file.name
            )
        
        # Add history records for both system and contract
        create_asset_history(
            asset_type='SYSTEM',
            asset=self.object.system,
            action='REGULAR_INSPECTION',
            user=self.request.user,
            comment=f'정기점검 등록: [{self.object.inspection_month}] {self.object.system.name} 정기점검'
        )
        
        create_asset_history(
            asset_type='CONTRACT',
            asset=self.object.contract,
            action='REGULAR_INSPECTION',
            user=self.request.user,
            comment=f'정기점검 등록: [{self.object.inspection_month}] {self.object.system.name} 정기점검'
        )
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': '점검 내역이 등록되었습니다.'})
            
        return response
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors})
        return super().form_invalid(form)

    def get_success_url(self):
        # Redirect back to the referring detail page
        referer = self.request.META.get('HTTP_REFERER')
        if referer and ('system' in referer or 'contract' in referer):
            return referer
        # Fallback
        if self.object.system:
            return reverse_lazy('assets:system_detail', kwargs={'pk': self.object.system.pk})
        return reverse_lazy('assets:contract_detail', kwargs={'pk': self.object.contract.pk})


class AssetTopologyView(LoginRequiredMixin, View):
    """자산 토폴로지 뷰 (Cytoscape.js 사용)"""
    def get(self, request):
        hide_unconnected = request.GET.get('hide_unconnected') == 'true'
        status_filter = request.GET.getlist('status')
        
        # 첫 진입 시(파라미터가 없을 때) 기본값 OPER 설정
        if not request.GET.get('status') and not request.GET.get('hide_unconnected'):
            status_filter = ['OPER']

        system_qs = System.objects.all()
        if status_filter:
            system_qs = system_qs.filter(status__in=status_filter)
        
        systems = system_qs
        contracts = Contract.objects.prefetch_related('systems', 'related_contracts')
        hardwares = Hardware.objects.prefetch_related('systems')
        softwares = Software.objects.prefetch_related('systems')

        nodes = []
        edges = []
        added_node_ids = set()
        system_nodes_with_edges = set()

        def add_node(id, label, type, status=None, display_status=None):
            if id not in added_node_ids:
                nodes.append({
                    'data': {
                        'id': id,
                        'label': label,
                        'type': type,
                        'status': status,
                        'display_status': display_status
                    }
                })
                added_node_ids.add(id)

        # 계약 노드 및 시스템 링크 준비
        contract_edges = []
        for c in contracts:
            c_systems = c.systems.filter(id__in=systems.values_list('id', flat=True))
            if c_systems.exists():
                add_node(f'con_{c.id}', c.name, 'contract', c.contract_type, c.get_contract_type_display())
                for s in c_systems:
                    contract_edges.append({
                        'data': {
                            'id': f'edge_con_{c.id}_sys_{s.id}',
                            'source': f'con_{c.id}',
                            'target': f'sys_{s.id}',
                            'type': 'contract_link'
                        }
                    })
                    system_nodes_with_edges.add(f'sys_{s.id}')
            
            # 연관계약 링크 (필터링된 시스템과 연결된 계약들 간의 관계만 표시)
            for rc in c.related_contracts.all():
                if f'con_{c.id}' in added_node_ids and f'con_{rc.id}' in added_node_ids:
                    src_id = min(c.id, rc.id)
                    tgt_id = max(c.id, rc.id)
                    edge_id = f"con_{src_id}_rel_con_{tgt_id}"
                    if not any(e['data']['id'] == edge_id for e in contract_edges):
                        contract_edges.append({
                            'data': {
                                'id': edge_id,
                                'source': f'con_{c.id}',
                                'target': f'con_{rc.id}',
                                'type': 'related_contract'
                            }
                        })

        # 하드웨어 노드 및 시스템 링크 준비
        hw_edges = []
        for h in hardwares:
            h_systems = h.systems.filter(id__in=systems.values_list('id', flat=True))
            if h_systems.exists():
                add_node(f'hw_{h.id}', h.name, 'hardware', h.status, h.get_status_display())
                for s in h_systems:
                    hw_edges.append({
                        'data': {
                            'id': f'edge_hw_{h.id}_sys_{s.id}',
                            'source': f'hw_{h.id}',
                            'target': f'sys_{s.id}',
                            'type': 'hardware_link'
                        }
                    })
                    system_nodes_with_edges.add(f'sys_{s.id}')

        # 소프트웨어 노드 및 시스템 링크 준비
        sw_edges = []
        for sw in softwares:
            sw_systems = sw.systems.filter(id__in=systems.values_list('id', flat=True))
            if sw_systems.exists():
                add_node(f'sw_{sw.id}', sw.name, 'software', sw.status, sw.get_status_display())
                for s in sw_systems:
                    sw_edges.append({
                        'data': {
                            'id': f'edge_sw_{sw.id}_sys_{s.id}',
                            'source': f'sw_{sw.id}',
                            'target': f'sys_{s.id}',
                            'type': 'software_link'
                        }
                    })
                    system_nodes_with_edges.add(f'sys_{s.id}')

        # 시스템 노드 추가 (최종 결정된 시스템들만)
        for s in systems:
            sys_id = f'sys_{s.id}'
            if not hide_unconnected or sys_id in system_nodes_with_edges:
                add_node(sys_id, s.name, 'system', s.status, s.get_status_display())

        # 모든 엣지 합치기 (노드가 존재하는 경우만)
        all_potential_edges = contract_edges + hw_edges + sw_edges
        for edge in all_potential_edges:
            if edge['data']['source'] in added_node_ids and edge['data']['target'] in added_node_ids:
                edges.append(edge)

        import json
        context = {
            'nodes_json': json.dumps(nodes),
            'edges_json': json.dumps(edges),
            'hide_unconnected': hide_unconnected,
            'current_statuses': status_filter,
            'status_choices': System.STATUS_CHOICES,
        }
        return render(request, 'assets/topology.html', context)
