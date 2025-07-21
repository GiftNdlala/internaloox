# Generated manually for frontend compatibility
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0006_update_product_model_for_mvp'),
    ]

    operations = [
        # Update Order model production status choices
        migrations.AlterField(
            model_name='order',
            name='production_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('not_started', '🟡 Not Started'),
                    ('cutting', '🔧 Cutting'),
                    ('sewing', '🧵 Sewing'),
                    ('finishing', '🎨 Finishing'),
                    ('quality_check', '🔍 Quality Check'),
                    ('completed', '✅ Completed'),
                    ('in_production', '🟠 In Production'),
                    ('ready_for_delivery', '🟢 Ready for Delivery'),
                ],
                default='not_started'
            ),
        ),
        
        # Update Order model payment status choices
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending'),
                    ('partial', 'Partial'),
                    ('paid', 'Paid'),
                    ('overdue', 'Overdue'),
                    ('deposit_only', 'Deposit Only'),
                    ('fifty_percent', '50% Paid'),
                    ('fully_paid', 'Fully Paid'),
                ],
                default='pending'
            ),
        ),
    ]