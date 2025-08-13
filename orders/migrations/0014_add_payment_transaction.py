from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0013_merge_conflicts'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_amount_delta', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('deposit_delta', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('balance_delta', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('amount_delta', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('previous_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('new_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('payment_method', models.CharField(blank=True, max_length=50, null=True)),
                ('payment_status', models.CharField(blank=True, max_length=20, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor_user', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, related_name='payment_transactions', to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='payment_transactions', to='orders.order')),
                ('proof', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='orders.paymentproof')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['order', 'created_at'], name='orders_pay_order_created_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['actor_user', 'created_at'], name='orders_pay_actor_created_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['payment_method'], name='orders_pay_method_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['payment_status'], name='orders_pay_status_idx'),
        ),
    ]