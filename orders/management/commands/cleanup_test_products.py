from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from orders.models import Product

class Command(BaseCommand):
    help = 'Clean up test products created by MVP data script while preserving color and fabric references'

    def handle(self, *args, **options):
        # Avoid non-ASCII output for Windows consoles
        self.stdout.write('Cleaning up test products...')
        
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
                # Match by either product_name or legacy name field
                qs = Product.objects.filter(Q(product_name=product_name) | Q(name=product_name))
                found = qs.count()
                if found:
                    num_deleted, _ = qs.delete()
                    deleted_count += num_deleted
                    self.stdout.write(f'  Deleted: {product_name} (rows: {num_deleted})')
                else:
                    self.stdout.write(f'  Not found: {product_name}')

            self.stdout.write('')
            self.stdout.write('Cleanup complete!')
            self.stdout.write(f'  - Total rows removed: {deleted_count}')
            self.stdout.write('  - Color and fabric references preserved')
            self.stdout.write('  - Database cleaned for production use')
