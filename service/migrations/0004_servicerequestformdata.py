# Generated manually for ServiceRequestFormData model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0003_alter_servicerequest_req_module_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceRequestFormData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataset', models.CharField(max_length=255, verbose_name='데이터셋 코드')),
                ('field_key', models.CharField(max_length=255, verbose_name='필드명')),
                ('field_value', models.TextField(blank=True, verbose_name='필드값')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('service_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='form_data', to='service.servicerequest')),
            ],
            options={
                'unique_together': {('service_request', 'field_key')},
            },
        ),
    ]
