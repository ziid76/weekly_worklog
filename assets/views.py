from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.core.paginator import Paginator
from .models import System, Contract, Hardware, Software, AssetHistory, ContractAttachment, RegularInspection, RegularInspectionAttachment
from .forms import SystemForm, ContractForm, HardwareForm, SoftwareForm, RegularInspectionForm
from .history_utils import create_asset_history
import os

class SystemListView(LoginRequiredMixin, ListView):
    model = System
    template_name = 'assets/system_list.html'
    context_object_name = 'systems'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q)
            )
        return queryset

class SystemDetailView(LoginRequiredMixin, DetailView):
    model = System
    template_name = 'assets/system_detail.html'
    context_object_name = 'system'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hardwares'] = self.object.hardwares.all()
        context['softwares'] = self.object.softwares.all()
        context['histories'] = self.object.histories.all()[:20]  # 최근 20개
        context['inspections'] = self.object.inspections.all()
        context['inspection_form'] = RegularInspectionForm(initial={'system': self.object})
        # Hide system field and filter contracts
        context['inspection_form'].fields['system'].widget.attrs['type'] = 'hidden'
        context['inspection_form'].fields['contract'].queryset = self.object.contracts.all()
        return context

class SystemCreateView(LoginRequiredMixin, CreateView):
    model = System
    form_class = SystemForm
    template_name = 'assets/system_form.html'
    success_url = reverse_lazy('assets:system_list')

class SystemUpdateView(LoginRequiredMixin, UpdateView):
    model = System
    form_class = SystemForm
    template_name = 'assets/system_form.html'
    
    def get_success_url(self):
        return reverse_lazy('assets:system_detail', kwargs={'pk': self.object.pk})

class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'assets/contract_list.html'
    context_object_name = 'contracts'
    ordering = ['-start_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        year = self.request.GET.get('year')
        
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
        context['year_range'] = sorted(years_set, reverse=True)
        
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
        context['inspection_form'].fields['contract'].widget.attrs['type'] = 'hidden'
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
