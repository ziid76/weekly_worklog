from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import monitor.models


def create_default_categories(apps, schema_editor):
    # Get the models
    LogCategory = apps.get_model('monitor', 'LogCategory')
    
    # Create default categories
    categories = [
        {
            'name': '운영 모니터링',
            'code': 'monitoring',
            'description': '시스템 운영 모니터링',
            'order': 1,
            'is_active': True
        },
        {
            'name': 'SAP 백업',
            'code': 'sap_backup',
            'description': 'SAP 시스템 백업',
            'order': 2,
            'is_active': True
        },
        {
            'name': '전산실 백업',
            'code': 'room_backup',
            'description': '전산실 시스템 백업',
            'order': 3,
            'is_active': True
        },
        {
            'name': '클라우드 백업',
            'code': 'cloud_backup',
            'description': '클라우드 시스템 백업',
            'order': 4,
            'is_active': True
        },
        {
            'name': '백업소산',
            'code': 'offsite_backup',
            'description': '백업 소산 작업',
            'order': 5,
            'is_active': True
        },
    ]
    
    for category_data in categories:
        LogCategory.objects.get_or_create(
            code=category_data['code'],
            defaults=category_data
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LogCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='카테고리명')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='카테고리 코드')),
                ('description', models.TextField(blank=True, verbose_name='설명')),
                ('order', models.IntegerField(default=0, verbose_name='정렬 순서')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성화')),
            ],
            options={
                'verbose_name': '로그 카테고리',
                'verbose_name_plural': '로그 카테고리',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='LogSubcategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='하위 카테고리명')),
                ('code', models.CharField(max_length=50, verbose_name='하위 카테고리 코드')),
                ('description', models.TextField(blank=True, verbose_name='설명')),
                ('order', models.IntegerField(default=0, verbose_name='정렬 순서')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성화')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='monitor.logcategory', verbose_name='카테고리')),
            ],
            options={
                'verbose_name': '로그 하위 카테고리',
                'verbose_name_plural': '로그 하위 카테고리',
                'ordering': ['category', 'order', 'name'],
                'unique_together': {('category', 'code')},
            },
        ),
        migrations.CreateModel(
            name='OperationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('approved', models.BooleanField(default=False)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_operation_logs', to=settings.AUTH_USER_MODEL)),
                ('completed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_operation_logs', to=settings.AUTH_USER_MODEL)),
                ('duty_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='duty_operation_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '운영 로그',
                'verbose_name_plural': '운영 로그',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.TextField(blank=True, verbose_name='점검 결과')),
                ('is_checked', models.BooleanField(default=False, verbose_name='점검완료')),
                ('checked_at', models.DateTimeField(blank=True, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_entries', to='monitor.logcategory')),
                ('checked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_entries', to=settings.AUTH_USER_MODEL)),
                ('operation_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_entries', to='monitor.operationlog')),
            ],
            options={
                'verbose_name': '로그 항목',
                'verbose_name_plural': '로그 항목',
                'unique_together': {('operation_log', 'category')},
            },
        ),
        migrations.CreateModel(
            name='OperationLogAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=monitor.models.operation_directory_path)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='monitor.operationlog')),
            ],
        ),
        migrations.CreateModel(
            name='SubcategoryEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.TextField(blank=True, verbose_name='점검 결과')),
                ('is_checked', models.BooleanField(default=False, verbose_name='점검완료')),
                ('log_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategory_entries', to='monitor.logentry')),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='monitor.logsubcategory')),
            ],
            options={
                'verbose_name': '하위 카테고리 항목',
                'verbose_name_plural': '하위 카테고리 항목',
                'unique_together': {('log_entry', 'subcategory')},
            },
        ),
        migrations.RunPython(create_default_categories),
    ]
