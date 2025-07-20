from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import ColorReference, FabricReference, Product

class Command(BaseCommand):
    help = 'Set up initial MVP reference data for colors, fabrics, and sample products'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up MVP reference data...'))
        
        with transaction.atomic():
            # Create Color References
            colors = [
                ('01', 'White', '#FFFFFF'),
                ('02', 'Black', '#000000'),
                ('03', 'Navy Blue', '#000080'),
                ('04', 'Brown', '#8B4513'),
                ('05', 'Grey', '#808080'),
                ('06', 'Beige', '#F5F5DC'),
                ('07', 'Red', '#FF0000'),
                ('08', 'Green', '#008000'),
                ('09', 'Blue', '#0000FF'),
                ('10', 'Cream', '#FFFDD0'),
            ]
            
            for code, name, hex_color in colors:
                color_ref, created = ColorReference.objects.get_or_create(
                    color_code=code,
                    defaults={'color_name': name, 'hex_color': hex_color}
                )
                if created:
                    self.stdout.write(f'  ✓ Created color: {code} - {name}')
                else:
                    self.stdout.write(f'  - Color exists: {code} - {name}')
            
            # Create Fabric References  
            fabrics = [
                ('A', 'Suede', 'Suede'),
                ('B', 'Leather', 'Genuine Leather'),
                ('C', 'Cotton', 'Cotton Blend'),
                ('D', 'Velvet', 'Velvet'),
                ('E', 'Linen', 'Linen'),
                ('F', 'Microfiber', 'Microfiber'),
                ('G', 'Canvas', 'Canvas'),
                ('H', 'Denim', 'Denim'),
                ('I', 'Silk', 'Silk'),
                ('J', 'Wool', 'Wool Blend'),
            ]
            
            for letter, name, fabric_type in fabrics:
                fabric_ref, created = FabricReference.objects.get_or_create(
                    fabric_letter=letter,
                    defaults={'fabric_name': name, 'fabric_type': fabric_type}
                )
                if created:
                    self.stdout.write(f'  ✓ Created fabric: {letter} - {name}')
                else:
                    self.stdout.write(f'  - Fabric exists: {letter} - {name}')
            
            # Create Sample Products
            sample_products = [
                {
                    'product_name': '3-Seater Couch',
                    'product_type': 'single',
                    'product_category': 'couch',
                    'default_fabric_letter': 'A',
                    'default_color_code': '03',
                    'unit_cost': 2500.00,
                    'unit_price': 4500.00,
                    'estimated_build_time': 7,
                    'description': 'Standard 3-seater couch with modern design'
                },
                {
                    'product_name': '2-Seater Couch',
                    'product_type': 'single', 
                    'product_category': 'couch',
                    'default_fabric_letter': 'A',
                    'default_color_code': '04',
                    'unit_cost': 2000.00,
                    'unit_price': 3500.00,
                    'estimated_build_time': 5,
                    'description': '2-seater couch perfect for smaller spaces'
                },
                {
                    'product_name': 'Coffee Table Set',
                    'product_type': 'set',
                    'product_category': 'coffee_table',
                    'default_fabric_letter': 'C',
                    'default_color_code': '04',
                    'unit_cost': 800.00,
                    'unit_price': 1500.00,
                    'estimated_build_time': 3,
                    'description': 'Modern coffee table with matching side tables'
                },
                {
                    'product_name': 'TV Stand',
                    'product_type': 'single',
                    'product_category': 'tv_stand', 
                    'default_fabric_letter': 'G',
                    'default_color_code': '02',
                    'unit_cost': 600.00,
                    'unit_price': 1200.00,
                    'estimated_build_time': 2,
                    'description': 'Modern TV stand with storage compartments'
                },
                {
                    'product_name': 'Queen Mattress',
                    'product_type': 'single',
                    'product_category': 'mattress',
                    'default_fabric_letter': 'F',
                    'default_color_code': '01',
                    'unit_cost': 1200.00,
                    'unit_price': 2200.00,
                    'estimated_build_time': 1,
                    'description': 'Queen size mattress with memory foam'
                }
            ]
            
            for product_data in sample_products:
                product, created = Product.objects.get_or_create(
                    product_name=product_data['product_name'],
                    defaults=product_data
                )
                if created:
                    self.stdout.write(f'  ✓ Created product: {product_data["product_name"]}')
                else:
                    self.stdout.write(f'  - Product exists: {product_data["product_name"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 MVP Reference data setup complete!\n'
                '   - Color codes: 01-10 available\n'
                '   - Fabric codes: A-J available\n' 
                '   - Sample products created\n'
                '   Ready for order placement testing!'
            )
        )