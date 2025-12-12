# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def migrate_form_elements_to_datasets(apps, schema_editor):
    """Migrate existing FormElement data to new Dataset structure"""
    FormElement = apps.get_model('service', 'FormElement')
    Dataset = apps.get_model('service', 'Dataset')
    
    # Get all existing form elements
    elements = FormElement.objects.all()
    
    # Create datasets from existing data and link elements
    for element in elements:
        if element.dataset_name and element.dataset_code:
            # Get or create dataset
            dataset, created = Dataset.objects.get_or_create(
                code=element.dataset_code,
                defaults={'name': element.dataset_name}
            )
            
            # Link element to dataset
            element.dataset = dataset
            element.save()


def reverse_migration(apps, schema_editor):
    """Reverse migration - populate old fields from dataset"""
    FormElement = apps.get_model('service', 'FormElement')
    
    for element in FormElement.objects.all():
        if element.dataset:
            element.dataset_name = element.dataset.name
            element.dataset_code = element.dataset.code
            element.save()


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0007_dataset_restructure'),
    ]

    operations = [
        # Migrate data
        migrations.RunPython(migrate_form_elements_to_datasets, reverse_migration),
        
        # Make dataset field required
        migrations.AlterField(
            model_name='formelement',
            name='dataset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='elements', to='service.dataset', verbose_name='데이터셋'),
        ),
        
        # Remove old fields
        migrations.RemoveField(
            model_name='formelement',
            name='dataset_name',
        ),
        migrations.RemoveField(
            model_name='formelement',
            name='dataset_code',
        ),
        
        # Add unique constraint
        migrations.AlterUniqueTogether(
            name='formelement',
            unique_together={('dataset', 'element_code')},
        ),
    ]
