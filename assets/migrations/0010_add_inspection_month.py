# Generated manually for inspection_month field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0009_regularinspection'),
    ]

    operations = [
        migrations.AddField(
            model_name='regularinspection',
            name='inspection_month',
            field=models.CharField(default='2024-01', help_text='YYYY-MM 형식', max_length=7, verbose_name='점검월'),
            preserve_default=False,
        ),
    ]
