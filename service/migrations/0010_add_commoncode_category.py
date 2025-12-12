# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0009_add_row_grouping'),
    ]

    operations = [
        migrations.AddField(
            model_name='commoncode',
            name='category',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='카테고리 구분자'),
        ),
        migrations.AddField(
            model_name='commoncode',
            name='display_order',
            field=models.IntegerField(default=0, verbose_name='표시 순서'),
        ),
        migrations.AlterModelOptions(
            name='commoncode',
            options={'ordering': ['category', 'display_order', 'name']},
        ),
    ]
