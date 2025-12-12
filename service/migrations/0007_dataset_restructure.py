# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0006_remove_unique_constraint'),
    ]

    operations = [
        # Create Dataset model
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='데이터셋 이름')),
                ('code', models.CharField(max_length=255, unique=True, verbose_name='데이터셋 코드')),
                ('description', models.TextField(blank=True, verbose_name='설명')),
                ('active', models.BooleanField(default=True, verbose_name='활성 여부')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        
        # Add dataset foreign key to FormElement (nullable first)
        migrations.AddField(
            model_name='formelement',
            name='dataset',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='elements', to='service.dataset', verbose_name='데이터셋'),
        ),
    ]
