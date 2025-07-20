# Generated manually for MVP updates
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_orderitem_product_description'),
    ]

    operations = [
        # First, add new MVP fields to Product
        migrations.AddField(
            model_name='product',
            name='product_name',
            field=models.CharField(max_length=200, default='Unnamed Product'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='default_fabric_letter',
            field=models.CharField(max_length=1, help_text="Default fabric code (A-Z)", default='A'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='default_color_code',
            field=models.CharField(max_length=2, help_text="Default color code (1-99)", default='01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='unit_cost',
            field=models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost to produce", default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='unit_price',
            field=models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price", default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='estimated_build_time',
            field=models.PositiveIntegerField(help_text="Days to build", default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='product',
            name='date_added',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        
        # Update product_type choices
        migrations.AlterField(
            model_name='product',
            name='product_type',
            field=models.CharField(max_length=32, choices=[('set', 'Set'), ('single', 'Single Item')]),
        ),
        
        # Add new reference tables
        migrations.CreateModel(
            name='ColorReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color_code', models.CharField(max_length=2, unique=True, help_text="Number code (1-99)")),
                ('color_name', models.CharField(max_length=50)),
                ('hex_color', models.CharField(blank=True, null=True, max_length=7, help_text="For digital reference #FFFFFF")),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['color_code'],
            },
        ),
        migrations.CreateModel(
            name='FabricReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fabric_letter', models.CharField(max_length=1, unique=True, help_text="Letter code (A-Z)")),
                ('fabric_name', models.CharField(max_length=50)),
                ('fabric_type', models.CharField(blank=True, null=True, max_length=50, help_text="e.g., Suede, Leather, Cotton")),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['fabric_letter'],
            },
        ),
        
        # Add MVP fields to Order
        migrations.AddField(
            model_name='order',
            name='customer_name',
            field=models.CharField(blank=True, null=True, max_length=200, help_text="Optional internal tracking"),
        ),
        migrations.AddField(
            model_name='order',
            name='production_status',
            field=models.CharField(max_length=20, choices=[('not_started', '🟡 Not Started'), ('in_production', '🟠 In Production'), ('ready_for_delivery', '🟢 Ready for Delivery')], default='not_started'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_deadline',
            field=models.DateField(help_text="Target delivery date", null=True),
        ),
        
        # Add MVP fields to OrderItem
        migrations.AddField(
            model_name='orderitem',
            name='assigned_fabric_letter',
            field=models.CharField(max_length=1, help_text="Fabric code from reference board", default='A'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='orderitem',
            name='assigned_color_code',
            field=models.CharField(max_length=2, help_text="Color code from reference board", default='01'),
            preserve_default=False,
        ),
    ]