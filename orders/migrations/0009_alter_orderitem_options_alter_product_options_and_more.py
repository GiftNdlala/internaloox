# Generated by Django 4.2.7 on 2025-07-21 21:03

from django.db import migrations, models
import django.db.models.deletion
import orders.models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_enhance_order_for_frontend'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orderitem',
            options={'verbose_name': 'Order Item', 'verbose_name_plural': 'Order Items'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterUniqueTogether(
            name='product',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='order',
            name='balance_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='orders.customer'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_deadline',
            field=models.DateField(default=orders.models.get_default_delivery_date, help_text='Target delivery date'),
        ),
        migrations.AlterField(
            model_name='order',
            name='deposit_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('in_production', 'In Production'), ('ready_for_delivery', 'Ready for Delivery'), ('out_for_delivery', 'Out for Delivery'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('partial', 'Partial'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('deposit_only', 'Deposit Only'), ('fifty_percent', '50% Paid'), ('fully_paid', 'Fully Paid')], default='deposit_only', max_length=20),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='date_added',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='default_color_code',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='default_fabric_letter',
            field=models.CharField(max_length=1),
        ),
        migrations.AlterField(
            model_name='product',
            name='default_quantity_unit',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='estimated_build_time',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='product',
            name='model_code',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_type',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='production_time_days',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_cost',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterModelTable(
            name='product',
            table='orders_product',
        ),
    ]
