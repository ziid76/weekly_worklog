# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0004_servicerequestformdata'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataset_name', models.CharField(max_length=255, verbose_name='데이터셋 이름')),
                ('dataset_code', models.CharField(max_length=255, verbose_name='데이터셋 코드')),
                ('element_name', models.CharField(max_length=255, verbose_name='폼 요소 이름')),
                ('element_code', models.CharField(max_length=255, verbose_name='폼 요소 코드')),
                ('element_type', models.CharField(choices=[('text', '텍스트'), ('textarea', '텍스트영역'), ('select', '선택박스'), ('checkbox', '체크박스'), ('radio', '라디오버튼'), ('number', '숫자'), ('date', '날짜'), ('email', '이메일')], max_length=20, verbose_name='폼 요소 유형')),
                ('element_options', models.TextField(blank=True, verbose_name='선택 옵션 (JSON)')),
                ('is_required', models.BooleanField(default=False, verbose_name='필수 여부')),
                ('placeholder', models.CharField(blank=True, max_length=255, verbose_name='플레이스홀더')),
                ('order', models.IntegerField(default=0, verbose_name='정렬 순서')),
                ('active', models.BooleanField(default=True, verbose_name='활성 여부')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['dataset_code', 'order'],
            },
        ),
        migrations.AddConstraint(
            model_name='formelement',
            constraint=models.UniqueConstraint(fields=('dataset_code', 'element_code'), name='unique_dataset_element'),
        ),
    ]
