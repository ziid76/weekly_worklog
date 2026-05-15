from django.db import models
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ReviewHistory
from .services import perform_code_review

class ReviewDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reviewer/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        filter_mine = self.request.GET.get('mine', '0') == '1'
        
        history = ReviewHistory.objects.all()
        
        if filter_mine:
            history = history.filter(created_by=self.request.user)
            
        if query:
            history = history.filter(
                models.Q(program_name__icontains=query) |
                models.Q(input_code__icontains=query) |
                models.Q(business_context__icontains=query)
            )
            
        context['history'] = history.order_by('-created_at')[:50]
        context['search_query'] = query
        context['filter_mine'] = filter_mine
        return context

class ReviewActionAPIView(LoginRequiredMixin, APIView):
    def post(self, request, *args, **kwargs):
        input_code = request.data.get('input_code')
        business_context = request.data.get('business_context', '')
        core_review_point = request.data.get('core_review_point', '')
        program_name = request.data.get('program_name', '')

        if not input_code:
            return Response({'error': 'Source code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # LLM 리뷰 수행
        review_result = perform_code_review(input_code, business_context, core_review_point)

        # 결과 저장
        history = ReviewHistory.objects.create(
            input_code=input_code,
            business_context=business_context,
            core_review_point=core_review_point,
            program_name=program_name,
            review_result=review_result,
            created_by=request.user
        )

        return Response({
            'id': history.id,
            'program_name': history.program_name,
            'review_result': review_result,
            'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

class ReviewDetailAPIView(LoginRequiredMixin, APIView):
    def get(self, request, pk, *args, **kwargs):
        history = get_object_or_404(ReviewHistory, pk=pk)
        return Response({
            'id': history.id,
            'program_name': history.program_name,
            'input_code': history.input_code,
            'business_context': history.business_context,
            'core_review_point': history.core_review_point,
            'review_result': history.review_result,
            'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': history.created_by.username if history.created_by else 'Anonymous'
        })
