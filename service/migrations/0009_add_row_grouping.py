# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0008_migrate_to_dataset_structure'),
    ]

    operations = [
        migrations.AddField(
            model_name='formelement',
            name='row_group',
            field=models.CharField(blank=True, max_length=50, verbose_name='행 그룹'),
        ),
        migrations.AddField(
            model_name='formelement',
            name='col_width',
            field=models.IntegerField(choices=[(12, '전체 (12/12)'), (6, '절반 (6/12)'), (4, '1/3 (4/12)'), (3, '1/4 (3/12)')], default=12, verbose_name='열 너비'),
        ),
    ]
