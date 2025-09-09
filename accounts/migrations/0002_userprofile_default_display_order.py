# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='default_display_order',
            field=models.IntegerField(default=0, help_text='주간보고서에서의 기본 표시 순서', verbose_name='기본 표시 순서'),
        ),
    ]
