from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0015_contract_manager'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='systems/%Y/%m/', verbose_name='파일')),
                ('filename', models.CharField(max_length=255, verbose_name='파일명')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='업로드일시')),
                ('description', models.TextField(blank=True, verbose_name='설명')),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='assets.system', verbose_name='시스템')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='업로더')),
            ],
            options={
                'verbose_name': '시스템 첨부파일',
                'verbose_name_plural': '시스템 첨부파일 목록',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
