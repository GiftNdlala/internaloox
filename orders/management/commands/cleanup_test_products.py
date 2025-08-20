from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Product

class Command(BaseCommand):
    help = 'Clean up test products created by MVP data script while preserving color and fabric references'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Cleaning up test products...'))
        
        # List of test product names to remove
        test_products = [
            'L-Shaped Corner Couch',
            '3-Seater Luxury Couch',
            '2-Seater Loveseat',
            'Recliner Couch Set',
            'Modern Glass Coffee Table',
            'Rustic Wood Coffee Table',
            'Coffee Table Set',
            'Modern TV Stand',
            'Corner TV Unit',
            'Entertainment Center',
            'Queen Memory Foam Mattress',
            'King Size Pillow Top Mattress',
            'Single Mattress',
            'Queen Wooden Base',
            'King Storage Base',
            'Complete Living Room Set',
            'Ottoman Storage Bench',
            'Accent Chair'
        ]
        
        with transaction.atomic():
            deleted_count = 0
            for product_name in test_products:
                try:
                    product = Product.objects.get(product_name=product_name)
                    product.delete()
                    self.stdout.write(f'  ✓ Deleted: {product_name}')
                    deleted_count += 1
                except Product.DoesNotExist:
                    self.stdout.write(f'  - Not found: {product_name}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Cleanup complete!\n'
                    f'   - {deleted_count} test products removed\n'
                    f'   - Color and fabric references preserved\n'
                    f'   - Database cleaned for production use'
                )
            )
