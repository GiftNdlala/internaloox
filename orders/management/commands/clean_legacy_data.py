from django.core.management.base import BaseCommand
from orders.models import Color, Fabric

class Command(BaseCommand):
    help = 'Delete legacy Color and Fabric records to start with clean slate'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning legacy Color and Fabric data...')
        
        # Delete legacy Color records
        color_count = Color.objects.count()
        Color.objects.all().delete()
        self.stdout.write(f'  ✓ Deleted {color_count} legacy Color records')
        
        # Delete legacy Fabric records
        fabric_count = Fabric.objects.count()
        Fabric.objects.all().delete()
        self.stdout.write(f'  ✓ Deleted {fabric_count} legacy Fabric records')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Clean slate achieved!\n'
                f'   - {color_count} legacy Color records removed\n'
                f'   - {fabric_count} legacy Fabric records removed\n'
                f'   - Ready to use ColorReference and FabricReference endpoints'
            )
        )
