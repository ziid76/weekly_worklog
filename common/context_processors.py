from service.models import ServiceRequest

def service_request_counts(request):
    if request.user.is_authenticated:
        # P: Processing (SR처리)
        # N: New (SR접수) - Assuming 'N' represents new requests to be received
        # A: Approved (SR승인) - Assuming 'A' represents requests waiting for approval
        
        # Adjust statuses based on your actual business logic
        # For example, if SR접수 means status='N' and assignee=user's team? 
        # Or simple global counts? 
        # Based on sidebar links:
        # SR 접수 -> service_request_reception_list (Usually status 'N' or 'A' depending on workflow)
        # SR 처리 -> service_request_list (Usually status 'P')
        # SR 승인 -> service_admin_approve_list (Usually status 'S' or 'A')

        # Let's assume generic filtering for now, adjust as per requirement
        # Counts for the current user or their team might be more appropriate
        
        # User specific counts (or team specific)
        count_reception = ServiceRequest.objects.filter(status='N', assignee=request.user).count() # 접수 대기
        count_processing = ServiceRequest.objects.filter(status='P', assignee=request.user).count() # 내가 처리중
        count_approval_user = ServiceRequest.objects.filter(status='A', assignee=request.user).count() # 승인 대기 
        count_approval = ServiceRequest.objects.filter(status='A').count() # 승인 대기
        
        return {
            'count_sr_reception': count_reception,
            'count_sr_processing': count_processing,
            'count_sr_approval': count_approval,
        }
    return {}
