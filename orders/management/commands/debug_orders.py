from django.core.management.base import BaseCommand
from orders.models import Order, OrderItem, Product
from django.db import connection


class Command(BaseCommand):
    help = 'Debug orders to understand why they have no items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix orders with missing items by creating sample items',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Starting order debugging...'))
        
        # Get all orders
        orders = Order.objects.all().prefetch_related('items')
        
        self.stdout.write(f'📊 Total orders found: {orders.count()}')
        
        orders_with_items = 0
        orders_without_items = 0
        problematic_orders = []
        
        for order in orders:
            item_count = order.items.count()
            
            if item_count > 0:
                orders_with_items += 1
                self.stdout.write(f'✅ Order {order.order_number} (ID: {order.id}) has {item_count} items')
            else:
                orders_without_items += 1
                problematic_orders.append(order)
                self.stdout.write(f'❌ Order {order.order_number} (ID: {order.id}) has NO items')
                
                # Check if this order has a total amount but no items
                if order.total_amount and order.total_amount > 0:
                    self.stdout.write(f'   💰 Order has total_amount: {order.total_amount} but no items!')
                
                # Check order status
                self.stdout.write(f'   📋 Order status: {order.order_status}, Production: {order.production_status}')
                
                # Check if order was created recently
                self.stdout.write(f'   🕒 Created: {order.created_at}')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'📈 Summary:')
        self.stdout.write(f'   Orders with items: {orders_with_items}')
        self.stdout.write(f'   Orders without items: {orders_without_items}')
        self.stdout.write(f'   Total orders: {orders.count()}')
        
        if problematic_orders:
            self.stdout.write(f'\n🚨 Problematic orders found: {len(problematic_orders)}')
            
            if options['fix']:
                self.stdout.write('\n🔧 Attempting to fix orders...')
                self.fix_orders(problematic_orders)
            else:
                self.stdout.write('\n💡 To attempt fixes, run: python manage.py debug_orders --fix')
        
        # Check database constraints
        self.check_database_integrity()
    
    def fix_orders(self, problematic_orders):
        """Attempt to fix orders by creating sample items"""
        # Get a sample product to use
        sample_product = Product.objects.first()
        
        if not sample_product:
            self.stdout.write(self.style.ERROR('❌ No products found in database. Cannot create sample items.'))
            return
        
        self.stdout.write(f'🔧 Using sample product: {sample_product.product_name} (ID: {sample_product.id})')
        
        fixed_count = 0
        for order in problematic_orders:
            try:
                # Create a sample order item
                OrderItem.objects.create(
                    order=order,
                    product=sample_product,
                    quantity=1,
                    unit_price=order.total_amount or 1000.00,  # Use order total or default
                    assigned_color_code='01',  # Default color code
                    assigned_fabric_letter='A',  # Default fabric letter
                    product_description=f'Sample item for order {order.order_number}'
                )
                
                self.stdout.write(f'✅ Fixed order {order.order_number} by adding sample item')
                fixed_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to fix order {order.order_number}: {e}'))
        
        self.stdout.write(f'\n🎯 Fixed {fixed_count} out of {len(problematic_orders)} problematic orders')
    
    def check_database_integrity(self):
        """Check database constraints and relationships"""
        self.stdout.write('\n🔍 Checking database integrity...')
        
        # Check if OrderItem table has any records
        item_count = OrderItem.objects.count()
        self.stdout.write(f'📦 Total OrderItems in database: {item_count}')
        
        # Check for orphaned OrderItems (items without orders)
        orphaned_items = OrderItem.objects.filter(order__isnull=True)
        if orphaned_items.exists():
            self.stdout.write(self.style.WARNING(f'⚠️  Found {orphaned_items.count()} orphaned OrderItems'))
        
        # Check for orders with invalid total amounts
        invalid_orders = Order.objects.filter(total_amount__lt=0)
        if invalid_orders.exists():
            self.stdout.write(self.style.WARNING(f'⚠️  Found {invalid_orders.count()} orders with negative total amounts'))
        
        # Check database constraints
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    tc.table_name, 
                    tc.constraint_name, 
                    tc.constraint_type,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name IN ('orders_order', 'orders_orderitem')
                ORDER BY tc.table_name, tc.constraint_type
            """)
            
            constraints = cursor.fetchall()
            if constraints:
                self.stdout.write(f'🔒 Database constraints found: {len(constraints)}')
                for constraint in constraints:
                    self.stdout.write(f'   {constraint[0]}.{constraint[1]} ({constraint[2]}) on {constraint[3]}')
