from django.db import migrations, models


def convert_versions(apps, schema_editor):
    WorkflowHistory = apps.get_model("vbpm", "WorkflowHistory")
    for history in WorkflowHistory.objects.all().order_by("id"):
        try:
            version_text = f"0.{int(history.version)}"
        except (TypeError, ValueError):
            version_text = "0.1"
        WorkflowHistory.objects.filter(pk=history.pk).update(version=version_text)


class Migration(migrations.Migration):
    dependencies = [
        ("vbpm", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workflowhistory",
            name="version",
            field=models.CharField(max_length=10, verbose_name="버전"),
        ),
        migrations.RunPython(convert_versions, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="workflowhistory",
            options={
                "ordering": ["-created_at", "-id"],
                "verbose_name": "워크플로우 이력",
                "verbose_name_plural": "워크플로우 이력 목록",
            },
        ),
    ]
