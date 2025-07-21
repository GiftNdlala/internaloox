from django.core.management.base import BaseCommand
from orders.models import Product
from django.db import connection

class Command(BaseCommand):
    help = 'Test Product model and database structure'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Testing Product model...')
        
        try:
            # Test 1: Check if we can query products
            product_count = Product.objects.count()
            self.stdout.write(f'✅ Product count: {product_count}')
            
            # Test 2: Try to get first product
            if product_count > 0:
                first_product = Product.objects.first()
                self.stdout.write(f'✅ First product: {first_product.name}')
                self.stdout.write(f'   - Price: {first_product.display_price}')
                self.stdout.write(f'   - Stock: {first_product.stock}')
                self.stdout.write(f'   - Created: {first_product.created_at}')
            
            # Test 3: Check database table structure
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'orders_product'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                
                self.stdout.write('📋 Database columns:')
                for col in columns:
                    self.stdout.write(f'   - {col[0]}: {col[1]} (nullable: {col[2]})')
            
            # Test 4: Try to create a simple product with correct field names
            test_product, created = Product.objects.get_or_create(
                name='Test Product API',
                defaults={
                    'description': 'Test product for API debugging',
                    'product_name': 'Test Product API',
                    'product_type': 'Test',
                    'default_fabric_letter': 'A',
                    'default_color_code': '01',
                    'unit_cost': 50.00,
                    'unit_price': 100.00,
                    'estimated_build_time': 7,
                    'stock': 1
                }
            )
            
            if created:
                self.stdout.write('✅ Created test product successfully')
            else:
                self.stdout.write('✅ Test product already exists')
                
            self.stdout.write('🎉 Product model test completed successfully!')
            
        except Exception as e:
            self.stdout.write(f'❌ Error: {str(e)}')
            self.stdout.write(f'❌ Error type: {type(e).__name__}')
            import traceback
            self.stdout.write(f'❌ Traceback: {traceback.format_exc()}')