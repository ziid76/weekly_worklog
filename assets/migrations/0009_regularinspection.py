# Generated manually for RegularInspection model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0008_alter_contracthistory_action_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegularInspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inspection_date', models.DateField(verbose_name='점검일자')),
                ('result', models.TextField(verbose_name='점검결과')),
                ('file', models.FileField(blank=True, null=True, upload_to='inspections/%Y/%m/', verbose_name='첨부파일')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='등록일시')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일시')),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspections', to='assets.contract', verbose_name='계약')),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspections', to='assets.system', verbose_name='시스템')),
            ],
            options={
                'verbose_name': '정기점검',
                'verbose_name_plural': '정기점검 목록',
                'ordering': ['-inspection_date', '-created_at'],
            },
        ),
    ]
