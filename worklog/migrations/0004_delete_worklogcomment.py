# Generated by Django 4.2.11 on 2025-07-07 07:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('worklog', '0003_worklogfile_worklogcomment'),
    ]

    operations = [
        migrations.DeleteModel(
            name='WorklogComment',
        ),
    ]
