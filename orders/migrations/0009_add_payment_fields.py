# Generated manually for payment fields
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0008_enhance_order_for_frontend'),
    ]

    operations = [
        # Add payment method field
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                max_length=50, 
                blank=True, 
                null=True, 
                help_text="Payment method used"
            ),
        ),
        
        # Add payment notes field
        migrations.AddField(
            model_name='order',
            name='payment_notes',
            field=models.TextField(
                blank=True, 
                null=True, 
                help_text="Additional payment notes"
            ),
        ),
    ]
