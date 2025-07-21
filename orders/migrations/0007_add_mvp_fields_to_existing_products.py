# Generated manually for MVP compatibility with existing database
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0006_update_product_model_for_mvp'),
    ]

    operations = [
        # Add MVP fields as optional to existing Product table
        migrations.AddField(
            model_name='product',
            name='product_name',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.CharField(max_length=32, choices=[('set', 'Set'), ('single', 'Single Item')], blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='product_category',
            field=models.CharField(max_length=100, choices=[('couch', 'Couch'), ('mattress', 'Mattress'), ('base', 'Base'), ('coffee_table', 'Coffee Table'), ('tv_stand', 'TV Stand'), ('accessory', 'Accessory'), ('other', 'Other')], blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='default_fabric_letter',
            field=models.CharField(max_length=1, blank=True, null=True, help_text="Default fabric code (A-Z)"),
        ),
        migrations.AddField(
            model_name='product',
            name='default_color_code',
            field=models.CharField(max_length=2, blank=True, null=True, help_text="Default color code (1-99)"),
        ),
        migrations.AddField(
            model_name='product',
            name='unit_cost',
            field=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Cost to produce"),
        ),
        migrations.AddField(
            model_name='product',
            name='unit_price',
            field=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Selling price"),
        ),
        migrations.AddField(
            model_name='product',
            name='estimated_build_time',
            field=models.PositiveIntegerField(blank=True, null=True, help_text="Days to build"),
        ),
        migrations.AddField(
            model_name='product',
            name='date_added',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='model_code',
            field=models.CharField(max_length=32, unique=True, blank=True, null=True),
        ),
        
        # Ensure core fields exist with defaults
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=200, default='Unnamed Product'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.CharField(max_length=50, default='R0.00'),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
    ]