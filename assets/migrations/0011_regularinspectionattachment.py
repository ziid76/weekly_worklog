# Generated manually for RegularInspectionAttachment model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0010_add_inspection_month'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegularInspectionAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='inspections/%Y/%m/', verbose_name='파일')),
                ('filename', models.CharField(max_length=255, verbose_name='파일명')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='업로드일시')),
                ('inspection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='assets.regularinspection', verbose_name='정기점검')),
            ],
            options={
                'verbose_name': '정기점검 첨부파일',
                'verbose_name_plural': '정기점검 첨부파일 목록',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
