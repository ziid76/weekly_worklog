from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from .models import System, Contract, Hardware, Software
from .history_utils import create_asset_history
from common.middleware import get_current_user

def get_changed_fields(old_instance, new_instance):
    """
    Compare old and new instance and return a dictionary of changed fields.
    """
    if not old_instance:
        return None
        
    changes = {}
    # Get all field names
    fields = [f.name for f in new_instance._meta.fields]
    
    for field in fields:
        # Skip auto_now and auto_now_add fields
        if field in ['created_at', 'updated_at']:
            continue
            
        old_value = getattr(old_instance, field)
        new_value = getattr(new_instance, field)
        
        if old_value != new_value:
            changes[field] = {
                'old': str(old_value) if old_value is not None else None,
                'new': str(new_value) if new_value is not None else None
            }
            
    return changes if changes else None

# --- System Signals ---

@receiver(pre_save, sender=System)
def track_system_old_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = System.objects.get(pk=instance.pk)
        except System.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None

@receiver(post_save, sender=System)
def log_system_changes(sender, instance, created, **kwargs):
    if created:
        create_asset_history(
            asset_type='SYSTEM',
            asset=instance,
            action='CREATE',
            user=get_current_user(),
            comment='시스템 생성'
        )
    elif hasattr(instance, '_old_instance') and instance._old_instance:
        changes = get_changed_fields(instance._old_instance, instance)
        if changes:
            create_asset_history(
                asset_type='SYSTEM',
                asset=instance,
                action='UPDATE',
                user=get_current_user(),
                changed_fields=changes,
                comment='시스템 정보 수정'
            )

# --- Contract Signals ---

@receiver(pre_save, sender=Contract)
def track_contract_old_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Contract.objects.get(pk=instance.pk)
        except Contract.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None

@receiver(post_save, sender=Contract)
def log_contract_changes(sender, instance, created, **kwargs):
    if created:
        create_asset_history(
            asset_type='CONTRACT',
            asset=instance,
            action='CREATE',
            user=get_current_user(),
            comment='계약 생성'
        )
    elif hasattr(instance, '_old_instance') and instance._old_instance:
        changes = get_changed_fields(instance._old_instance, instance)
        if changes:
            create_asset_history(
                asset_type='CONTRACT',
                asset=instance,
                action='UPDATE',
                user=get_current_user(),
                changed_fields=changes,
                comment='계약 정보 수정'
            )

@receiver(m2m_changed, sender=Contract.systems.through)
def log_contract_system_changes(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Track changes in Contract-System relationship."""
    if action not in ['post_add', 'post_remove']:
        return

    if reverse:
        # instance is System, pk_set contains Contract IDs
        contracts = Contract.objects.filter(pk__in=pk_set)
        for contract in contracts:
            history_action = 'SYSTEM_ADD' if action == 'post_add' else 'SYSTEM_REMOVE'
            create_asset_history(
                asset_type='CONTRACT',
                asset=contract,
                action=history_action,
                user=get_current_user(),
                related_system=instance,
                comment=f"시스템 {instance.name} {'연결' if action == 'post_add' else '해제'}"
            )
            # Also log to System
            sys_action = 'CONTRACT_ADD' if action == 'post_add' else 'CONTRACT_REMOVE'
            create_asset_history(
                asset_type='SYSTEM',
                asset=instance,
                action=sys_action,
                user=get_current_user(),
                related_contract=contract,
                comment=f"계약 {contract.name} {'연결' if action == 'post_add' else '해제'}"
            )
    else:
        # instance is Contract, pk_set contains System IDs
        systems = System.objects.filter(pk__in=pk_set)
        for system in systems:
            history_action = 'SYSTEM_ADD' if action == 'post_add' else 'SYSTEM_REMOVE'
            create_asset_history(
                asset_type='CONTRACT',
                asset=instance,
                action=history_action,
                user=get_current_user(),
                related_system=system,
                comment=f"시스템 {system.name} {'연결' if action == 'post_add' else '해제'}"
            )
            # Also log to System
            sys_action = 'CONTRACT_ADD' if action == 'post_add' else 'CONTRACT_REMOVE'
            create_asset_history(
                asset_type='SYSTEM',
                asset=system,
                action=sys_action,
                user=get_current_user(),
                related_contract=instance,
                comment=f"계약 {instance.name} {'연결' if action == 'post_add' else '해제'}"
            )

@receiver(m2m_changed, sender=Contract.related_contracts.through)
def log_contract_link_changes(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action not in ['post_add', 'post_remove']:
        return
        
    targets = Contract.objects.filter(pk__in=pk_set)
    for target in targets:
        history_action = 'LINK_CONTRACT_ADD' if action == 'post_add' else 'LINK_CONTRACT_REMOVE'
        
        # Log for source contract
        create_asset_history(
            asset_type='CONTRACT',
            asset=instance,
            action=history_action,
            user=get_current_user(),
            related_contract=target,
            comment=f"연관계약 {target.name} {'연결' if action == 'post_add' else '해제'}"
        )
        
        # Log for target contract
        create_asset_history(
            asset_type='CONTRACT',
            asset=target,
            action=history_action,
            user=get_current_user(),
            related_contract=instance,
            comment=f"연관계약 {instance.name} {'연결' if action == 'post_add' else '해제'}"
        )


# --- Hardware Signals ---

@receiver(pre_save, sender=Hardware)
def track_hardware_old_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Hardware.objects.get(pk=instance.pk)
        except Hardware.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None

@receiver(post_save, sender=Hardware)
def log_hardware_changes(sender, instance, created, **kwargs):
    if created:
        create_asset_history(
            asset_type='HARDWARE',
            asset=instance,
            action='CREATE',
            user=get_current_user(),
            comment='하드웨어 생성'
        )
    elif hasattr(instance, '_old_instance') and instance._old_instance:
        changes = get_changed_fields(instance._old_instance, instance)
        if changes:
            create_asset_history(
                asset_type='HARDWARE',
                asset=instance,
                action='UPDATE',
                user=get_current_user(),
                changed_fields=changes,
                comment='하드웨어 정보 수정'
            )

@receiver(m2m_changed, sender=Hardware.systems.through)
def log_hardware_system_changes(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action not in ['post_add', 'post_remove']:
        return

    if reverse:
        # instance is System, pk_set contains Hardware IDs
        hardwares = Hardware.objects.filter(pk__in=pk_set)
        for hardware in hardwares:
            history_action = 'SYSTEM_ADD' if action == 'post_add' else 'SYSTEM_REMOVE'
            create_asset_history(
                asset_type='HARDWARE',
                asset=hardware,
                action=history_action,
                user=get_current_user(),
                related_system=instance,
                comment=f"시스템 {instance.name} {'연결' if action == 'post_add' else '해제'}"
            )
            # Log to System
            sys_action = 'HARDWARE_ADD' if action == 'post_add' else 'HARDWARE_REMOVE'
            create_asset_history(
                asset_type='SYSTEM',
                asset=instance,
                action=sys_action,
                user=get_current_user(),
                related_hardware=hardware,
                comment=f"하드웨어 {hardware.name} {'연결' if action == 'post_add' else '해제'}"
            )
    else:
        # instance is Hardware, pk_set contains System IDs
        systems = System.objects.filter(pk__in=pk_set)
        for system in systems:
            history_action = 'SYSTEM_ADD' if action == 'post_add' else 'SYSTEM_REMOVE'
            create_asset_history(
                asset_type='HARDWARE',
                asset=instance,
                action=history_action,
                user=get_current_user(),
                related_system=system,
                comment=f"시스템 {system.name} {'연결' if action == 'post_add' else '해제'}"
            )
            # Log to System
            sys_action = 'HARDWARE_ADD' if action == 'post_add' else 'HARDWARE_REMOVE'
            create_asset_history(
                asset_type='SYSTEM',
                asset=system,
                action=sys_action,
                user=get_current_user(),
                related_hardware=instance,
                comment=f"하드웨어 {instance.name} {'연결' if action == 'post_add' else '해제'}"
            )


# --- Software Signals ---

@receiver(pre_save, sender=Software)
def track_software_old_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Software.objects.get(pk=instance.pk)
        except Software.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None

@receiver(post_save, sender=Software)
def log_software_changes(sender, instance, created, **kwargs):
    if created:
        create_asset_history(
            asset_type='SOFTWARE',
            asset=instance,
            action='CREATE',
            user=get_current_user(),
            comment='소프트웨어 생성'
        )
    elif hasattr(instance, '_old_instance') and instance._old_instance:
        changes = get_changed_fields(instance._old_instance, instance)
        if changes:
            create_asset_history(
                asset_type='SOFTWARE',
                asset=instance,
                action='UPDATE',
                user=get_current_user(),
                changed_fields=changes,
                comment='소프트웨어 정보 수정'
            )

@receiver(m2m_changed, sender=Software.systems.through)
def log_software_system_changes(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action not in ['post_add', 'post_remove']:
        return

    if reverse:
        # instance is System, pk_set contains Software IDs
        softwares = Software.objects.filter(pk__in=pk_set)
        for software in softwares:
            history_action = 'SYSTEM_ADD' if action == 'post_add' else 'SYSTEM_REMOVE'
            create_asset_history(
                asset_type='SOFTWARE',
                asset=software,
                action=history_action,
                user=get_current_user(),
                related_system=instance,
                comment=f"시스템 {instance.name} {'연결' if action == 'post_add' else '해제'}"
            )
            # Log to System
            sys_action = 'SOFTWARE_ADD' if action == 'post_add' else 'SOFTWARE_REMOVE'
            create_asset_history(
                asset_type='SYSTEM',
                asset=instance,
                action=sys_action,
                user=get_current_user(),
                related_software=software,
                comment=f"소프트웨어 {software.name} {'연결' if action == 'post_add' else '해제'}"
            )
    else:
        # instance is Software, pk_set contains System IDs
        systems = System.objects.filter(pk__in=pk_set)
        for system in systems:
            history_action = 'SYSTEM_ADD' if action == 'post_add' else 'SYSTEM_REMOVE'
            create_asset_history(
                asset_type='SOFTWARE',
                asset=instance,
                action=history_action,
                user=get_current_user(),
                related_system=system,
                comment=f"시스템 {system.name} {'연결' if action == 'post_add' else '해제'}"
            )
            # Log to System
            sys_action = 'SOFTWARE_ADD' if action == 'post_add' else 'SOFTWARE_REMOVE'
            create_asset_history(
                asset_type='SYSTEM',
                asset=system,
                action=sys_action,
                user=get_current_user(),
                related_software=instance,
                comment=f"소프트웨어 {instance.name} {'연결' if action == 'post_add' else '해제'}"
            )
