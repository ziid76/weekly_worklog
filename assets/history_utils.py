"""
Helper utilities for creating AssetHistory records
"""
from .models import AssetHistory


def create_asset_history(asset_type, asset, action, user=None, comment='', **kwargs):
    """
    Create an AssetHistory record
    
    Args:
        asset_type: 'SYSTEM', 'CONTRACT', 'HARDWARE', or 'SOFTWARE'
        asset: The asset object (System, Contract, Hardware, or Software instance)
        action: Action code (e.g., 'CREATE', 'UPDATE', etc.)
        user: User who performed the action
        comment: Comment about the action
        **kwargs: Additional fields (related_system, related_contract, changed_fields, etc.)
    
    Returns:
        AssetHistory instance
    """
    history_data = {
        'asset_type': asset_type,
        'action': action,
        'user': user,
        'comment': comment,
    }
    
    # Set the appropriate asset field
    if asset_type == 'SYSTEM':
        history_data['system'] = asset
    elif asset_type == 'CONTRACT':
        history_data['contract'] = asset
    elif asset_type == 'HARDWARE':
        history_data['hardware'] = asset
    elif asset_type == 'SOFTWARE':
        history_data['software'] = asset
    
    # Add any additional fields
    history_data.update(kwargs)
    
    return AssetHistory.objects.create(**history_data)
