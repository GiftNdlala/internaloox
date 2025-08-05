from django.core.management.base import BaseCommand
from inventory.models import MaterialCategory, Supplier, Material


class Command(BaseCommand):
    help = 'Set up initial inventory data for warehouse management'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial inventory data...')
        
        # Create material categories
        categories_data = [
            ('foam', 'Foam materials for cushioning'),
            ('wood', 'Wood and board materials for structure'),
            ('fabric', 'Fabric materials for upholstery'),
            ('accessories', 'Hardware and accessories'),
            ('packaging', 'Packaging materials'),
        ]
        
        for category_name, description in categories_data:
            category, created = MaterialCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'  ✓ Created category: {category.get_name_display()}')
            else:
                self.stdout.write(f'  - Category exists: {category.get_name_display()}')
        
        # Create sample suppliers
        suppliers_data = [
            {
                'name': 'Foam Solutions SA',
                'contact_person': 'John Smith',
                'phone': '011-123-4567',
                'email': 'orders@foamsolutions.co.za',
                'address': '123 Industrial Road, Johannesburg'
            },
            {
                'name': 'Timber & Boards Co',
                'contact_person': 'Mary Johnson',
                'phone': '021-987-6543',
                'email': 'sales@timberboards.co.za',
                'address': '456 Wood Street, Cape Town'
            },
            {
                'name': 'Premium Fabrics',
                'contact_person': 'David Wilson',
                'phone': '031-555-7890',
                'email': 'info@premiumfabrics.co.za',
                'address': '789 Textile Avenue, Durban'
            },
            {
                'name': 'Hardware Supplies',
                'contact_person': 'Sarah Brown',
                'phone': '011-222-3333',
                'email': 'orders@hardwaresupplies.co.za',
                'address': '321 Hardware Lane, Pretoria'
            }
        ]
        
        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults=supplier_data
            )
            if created:
                self.stdout.write(f'  ✓ Created supplier: {supplier.name}')
            else:
                self.stdout.write(f'  - Supplier exists: {supplier.name}')
        
        # Create sample materials
        foam_category = MaterialCategory.objects.get(name='foam')
        wood_category = MaterialCategory.objects.get(name='wood')
        fabric_category = MaterialCategory.objects.get(name='fabric')
        accessories_category = MaterialCategory.objects.get(name='accessories')
        packaging_category = MaterialCategory.objects.get(name='packaging')
        
        foam_supplier = Supplier.objects.get(name='Foam Solutions SA')
        wood_supplier = Supplier.objects.get(name='Timber & Boards Co')
        fabric_supplier = Supplier.objects.get(name='Premium Fabrics')
        hardware_supplier = Supplier.objects.get(name='Hardware Supplies')
        
        materials_data = [
            # Foam materials
            {
                'name': 'High Density Foam - 2 inch',
                'category': foam_category,
                'unit': 'pieces',
                'current_stock': 50,
                'minimum_stock': 10,
                'ideal_stock': 100,
                'cost_per_unit': 45.00,
                'primary_supplier': foam_supplier,
                'color_variants': 'White, Beige',
                'quality_grade': 'High Density'
            },
            {
                'name': 'Medium Density Foam - 4 inch',
                'category': foam_category,
                'unit': 'pieces',
                'current_stock': 30,
                'minimum_stock': 8,
                'ideal_stock': 60,
                'cost_per_unit': 65.00,
                'primary_supplier': foam_supplier,
                'color_variants': 'White, Yellow',
                'quality_grade': 'Medium Density'
            },
            # Wood materials
            {
                'name': 'Masonite Board - 4x8ft',
                'category': wood_category,
                'unit': 'boards',
                'current_stock': 25,
                'minimum_stock': 5,
                'ideal_stock': 50,
                'cost_per_unit': 120.00,
                'primary_supplier': wood_supplier,
                'quality_grade': 'Standard'
            },
            {
                'name': 'Pine Wood Strips - 2x4',
                'category': wood_category,
                'unit': 'pieces',
                'current_stock': 40,
                'minimum_stock': 10,
                'ideal_stock': 80,
                'cost_per_unit': 35.00,
                'primary_supplier': wood_supplier,
                'quality_grade': 'Premium Pine'
            },
            # Fabric materials
            {
                'name': 'Suede Fabric',
                'category': fabric_category,
                'unit': 'meters',
                'current_stock': 150,
                'minimum_stock': 30,
                'ideal_stock': 300,
                'cost_per_unit': 85.00,
                'primary_supplier': fabric_supplier,
                'color_variants': 'Navy Blue, Brown, Grey, Black, Beige',
                'quality_grade': 'Premium Suede'
            },
            {
                'name': 'Canvas Fabric',
                'category': fabric_category,
                'unit': 'meters',
                'current_stock': 200,
                'minimum_stock': 40,
                'ideal_stock': 400,
                'cost_per_unit': 65.00,
                'primary_supplier': fabric_supplier,
                'color_variants': 'Natural, White, Khaki, Dark Blue',
                'quality_grade': 'Heavy Duty Canvas'
            },
            {
                'name': 'Leatherette',
                'category': fabric_category,
                'unit': 'meters',
                'current_stock': 80,
                'minimum_stock': 20,
                'ideal_stock': 160,
                'cost_per_unit': 120.00,
                'primary_supplier': fabric_supplier,
                'color_variants': 'Black, Brown, White, Red',
                'quality_grade': 'Synthetic Leather'
            },
            # Accessories
            {
                'name': 'Heavy Duty Staples',
                'category': accessories_category,
                'unit': 'units',
                'current_stock': 5000,
                'minimum_stock': 1000,
                'ideal_stock': 10000,
                'cost_per_unit': 0.15,
                'primary_supplier': hardware_supplier,
                'quality_grade': 'Industrial Grade'
            },
            {
                'name': 'Furniture Glue',
                'category': accessories_category,
                'unit': 'liters',
                'current_stock': 20,
                'minimum_stock': 5,
                'ideal_stock': 40,
                'cost_per_unit': 45.00,
                'primary_supplier': hardware_supplier,
                'quality_grade': 'Professional Grade'
            },
            {
                'name': 'Metal Zippers - 20cm',
                'category': accessories_category,
                'unit': 'units',
                'current_stock': 200,
                'minimum_stock': 50,
                'ideal_stock': 500,
                'cost_per_unit': 8.50,
                'primary_supplier': hardware_supplier,
                'color_variants': 'Black, Brown, Silver',
                'quality_grade': 'Heavy Duty'
            },
            # Packaging
            {
                'name': 'Furniture Wrap - Large',
                'category': packaging_category,
                'unit': 'rolls',
                'current_stock': 15,
                'minimum_stock': 3,
                'ideal_stock': 30,
                'cost_per_unit': 25.00,
                'primary_supplier': hardware_supplier,
                'quality_grade': 'Heavy Duty Plastic'
            },
            {
                'name': 'Cardboard Boxes - Large',
                'category': packaging_category,
                'unit': 'units',
                'current_stock': 100,
                'minimum_stock': 20,
                'ideal_stock': 200,
                'cost_per_unit': 12.00,
                'primary_supplier': hardware_supplier,
                'quality_grade': 'Double Wall Corrugated'
            }
        ]
        
        for material_data in materials_data:
            material, created = Material.objects.get_or_create(
                name=material_data['name'],
                category=material_data['category'],
                defaults=material_data
            )
            if created:
                self.stdout.write(f'  ✓ Created material: {material.name}')
            else:
                self.stdout.write(f'  - Material exists: {material.name}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Inventory setup completed successfully!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Run migrations: python manage.py makemigrations && python manage.py migrate')
        self.stdout.write('2. Set up product-material relationships using ProductMaterial model')
        self.stdout.write('3. Configure task types for warehouse operations')
        self.stdout.write('4. Test the API endpoints for inventory management')