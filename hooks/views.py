from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import WebhookSource, WebhookEvent, Incident, IncidentEvent
import json
import logging
import hashlib
from django.utils import timezone

logger = logging.getLogger(__name__)

# --- Webhook Endpoints ---

@csrf_exempt
@require_POST
def webhook_receive(request, source_key):
    """Generic or specific webhook receiver"""
    try:
        source = WebhookSource.objects.get(source_key=source_key, is_active=True)
    except WebhookSource.DoesNotExist:
        return HttpResponse(status=404)
    
    # Token auth (Simple)
    token = request.headers.get('X-Webhook-Token') or request.GET.get('token')
    if source.secret_token and token != source.secret_token:
        return HttpResponse(status=403)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    # Save raw event
    event = WebhookEvent.objects.create(
        source=source,
        payload=payload,
        headers=dict(request.headers),
        external_uuid=payload.get('uuid')
    )
    
    # Deduplication check
    if payload.get('uuid'):
        if WebhookEvent.objects.filter(source=source, external_uuid=payload.get('uuid'), processed=True).exclude(id=event.id).exists():
            event.processed = True
            event.save()
            return JsonResponse({"status": "ignored", "reason": "duplicate uuid"})

    # Process based on source type
    if source.source_type == 'whatap':
        process_whatap_incident(event)
    
    return JsonResponse({"status": "success", "event_id": event.id})

def process_whatap_incident(event):
    payload = event.payload
    source = event.source
    
    # Generate fingerprint
    pcode = payload.get('pcode', '')
    oid = payload.get('oid', '')
    metric = payload.get('metricName', '')
    title = payload.get('title', '')
    
    fp_raw = f"whatap-{pcode}-{oid}-{metric}-{title}"
    fingerprint = hashlib.sha256(fp_raw.encode()).hexdigest()
    
    status_map = {
        'OPEN': 'open',
        'RESOLVED': 'resolved',
        'OK': 'resolved',
        'NORMAL': 'resolved',
    }
    new_status = status_map.get(payload.get('status', '').upper(), 'open')
    level = payload.get('level', 'warning').lower()
    if level not in ['info', 'warning', 'critical', 'fatal']:
        level = 'warning'

    # Upsert Incident
    incident = Incident.objects.filter(fingerprint=fingerprint).first()
    
    if not incident:
        incident = Incident.objects.create(
            fingerprint=fingerprint,
            title=title,
            description=payload.get('message', ''),
            status=new_status,
            level=level,
            source=source,
            projectName=payload.get('projectName', ''),
            oname=payload.get('oname', ''),
            metricName=metric,
        )
        IncidentEvent.objects.create(
            incident=incident,
            event_type='created',
            message=f"인시던트가 생성되었습니다. (Level: {level})",
            raw_event=event
        )
    else:
        old_status = incident.status
        incident.title = title
        incident.description = payload.get('message', '')
        incident.status = new_status
        incident.level = level
        incident.updated_at = timezone.now()
        
        if new_status == 'resolved' and old_status != 'resolved':
            incident.resolved_at = timezone.now()
        
        incident.save()
        
        # Log change if status changed or just log the reception
        msg = f"웹훅 수신: {new_status}"
        if old_status != new_status:
            msg = f"상태 변경: {old_status} -> {new_status}"
            
        IncidentEvent.objects.create(
            incident=incident,
            event_type='webhook_received',
            message=msg,
            raw_event=event
        )

    event.processed = True
    event.save()

# --- UI Views ---

@login_required
def incident_list(request):
    incidents = Incident.objects.all()
    status_filter = request.GET.get('status')
    if status_filter:
        incidents = incidents.filter(status=status_filter)
    
    return render(request, 'hooks/incident_list.html', {
        'incidents': incidents,
        'status_filter': status_filter
    })

@login_required
def incident_detail(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    events = incident.events.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_status':
            new_status = request.POST.get('status')
            old_status = incident.status
            incident.status = new_status
            if new_status == 'resolved':
                incident.resolved_at = timezone.now()
            incident.save()
            
            IncidentEvent.objects.create(
                incident=incident,
                event_type='status_changed',
                message=f"사용자에 의해 상태가 변경되었습니다: {old_status} -> {new_status}",
                user=request.user
            )
        elif action == 'add_comment':
            comment = request.POST.get('comment')
            if comment:
                IncidentEvent.objects.create(
                    incident=incident,
                    event_type='commented',
                    message=comment,
                    user=request.user
                )
        return redirect('hooks:incident_detail', pk=pk)

    return render(request, 'hooks/incident_detail.html', {
        'incident': incident,
        'events': events
    })

@login_required
def source_list(request):
    sources = WebhookSource.objects.all()
    return render(request, 'hooks/source_list.html', {'sources': sources})

@login_required
def source_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        source_type = request.POST.get('source_type', 'whatap')
        secret_token = request.POST.get('secret_token')
        
        WebhookSource.objects.create(
            name=name,
            source_type=source_type,
            secret_token=secret_token
        )
        return redirect('hooks:source_list')
    
    return render(request, 'hooks/source_form.html')
