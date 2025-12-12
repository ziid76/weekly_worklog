# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0005_formelement'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='formelement',
            name='unique_dataset_element',
        ),
    ]
