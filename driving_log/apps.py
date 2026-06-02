from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _ensure_driving_log_groups(sender, **kwargs):
    """driving_log_users / driving_log_managers 그룹을 첫 migrate 시 자동 생성."""
    if sender.name != 'driving_log':
        return
    from django.contrib.auth.models import Group
    from .permissions import DRIVING_LOG_USER_GROUP, DRIVING_LOG_MANAGER_GROUP
    Group.objects.get_or_create(name=DRIVING_LOG_USER_GROUP)
    Group.objects.get_or_create(name=DRIVING_LOG_MANAGER_GROUP)


class DrivingLogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'driving_log'
    verbose_name = '운행일지'

    def ready(self):
        post_migrate.connect(_ensure_driving_log_groups, sender=self)
