# Generated manually to remove category requirement
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        # Make category field optional
        migrations.AlterField(
            model_name='material',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='materials',
                to='inventory.materialcategory'
            ),
        ),
        # Remove unique constraint on name + category
        migrations.AlterUniqueTogether(
            name='material',
            unique_together=set(),
        ),
        # Add unique constraint on name only
        migrations.AlterUniqueTogether(
            name='material',
            unique_together={('name',)},
        ),
    ]
