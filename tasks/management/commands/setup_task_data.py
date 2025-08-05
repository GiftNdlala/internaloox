from django.core.management.base import BaseCommand
from tasks.models import TaskType, TaskTemplate, TaskTemplateStep
from datetime import timedelta


class Command(BaseCommand):
    help = 'Set up initial task types and templates for warehouse operations'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial task data...')
        
        # Create task types based on production workflow
        task_types_data = [
            {
                'name': 'Material Preparation',
                'description': 'Prepare and gather materials for production',
                'estimated_duration_minutes': 30,
                'requires_materials': True,
                'sequence_order': 1
            },
            {
                'name': 'Cutting',
                'description': 'Cut materials according to specifications',
                'estimated_duration_minutes': 60,
                'requires_materials': True,
                'sequence_order': 2
            },
            {
                'name': 'Frame Assembly',
                'description': 'Assemble wooden frame structure',
                'estimated_duration_minutes': 90,
                'requires_materials': True,
                'sequence_order': 3
            },
            {
                'name': 'Foam Installation',
                'description': 'Install foam padding and cushioning',
                'estimated_duration_minutes': 45,
                'requires_materials': True,
                'sequence_order': 4
            },
            {
                'name': 'Upholstery',
                'description': 'Apply fabric covering and upholstery work',
                'estimated_duration_minutes': 120,
                'requires_materials': True,
                'sequence_order': 5
            },
            {
                'name': 'Finishing',
                'description': 'Final touches, trimming, and detail work',
                'estimated_duration_minutes': 60,
                'requires_materials': True,
                'sequence_order': 6
            },
            {
                'name': 'Quality Check',
                'description': 'Inspect finished product for quality',
                'estimated_duration_minutes': 30,
                'requires_materials': False,
                'sequence_order': 7
            },
            {
                'name': 'Packaging',
                'description': 'Package product for delivery',
                'estimated_duration_minutes': 20,
                'requires_materials': True,
                'sequence_order': 8
            },
            {
                'name': 'Stock Management',
                'description': 'Update inventory and stock levels',
                'estimated_duration_minutes': 15,
                'requires_materials': False,
                'sequence_order': 9
            },
            {
                'name': 'Maintenance',
                'description': 'Equipment and workspace maintenance',
                'estimated_duration_minutes': 45,
                'requires_materials': False,
                'sequence_order': 10
            }
        ]
        
        for task_type_data in task_types_data:
            task_type, created = TaskType.objects.get_or_create(
                name=task_type_data['name'],
                defaults=task_type_data
            )
            if created:
                self.stdout.write(f'  ✓ Created task type: {task_type.name}')
            else:
                self.stdout.write(f'  - Task type exists: {task_type.name}')
        
        # Create task templates for common furniture types
        self.stdout.write('\nCreating task templates...')
        
        # Get task types for template creation
        material_prep = TaskType.objects.get(name='Material Preparation')
        cutting = TaskType.objects.get(name='Cutting')
        frame_assembly = TaskType.objects.get(name='Frame Assembly')
        foam_installation = TaskType.objects.get(name='Foam Installation')
        upholstery = TaskType.objects.get(name='Upholstery')
        finishing = TaskType.objects.get(name='Finishing')
        quality_check = TaskType.objects.get(name='Quality Check')
        packaging = TaskType.objects.get(name='Packaging')
        
        # Couch/Sofa Template
        couch_template, created = TaskTemplate.objects.get_or_create(
            name='Standard Couch Production',
            defaults={
                'description': 'Complete production workflow for standard couches and sofas',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Created template: {couch_template.name}')
            
            # Create template steps for couch
            couch_steps = [
                (material_prep, 1, timedelta(minutes=45), 'Gather foam, fabric, wood, and hardware'),
                (cutting, 2, timedelta(minutes=90), 'Cut fabric and foam to specifications'),
                (frame_assembly, 3, timedelta(minutes=120), 'Build wooden frame structure'),
                (foam_installation, 4, timedelta(minutes=60), 'Install foam padding and cushions'),
                (upholstery, 5, timedelta(minutes=180), 'Apply fabric covering and upholstery'),
                (finishing, 6, timedelta(minutes=90), 'Add finishing touches and trim'),
                (quality_check, 7, timedelta(minutes=30), 'Final quality inspection'),
                (packaging, 8, timedelta(minutes=30), 'Package for delivery')
            ]
            
            for task_type, sequence, duration, description in couch_steps:
                TaskTemplateStep.objects.create(
                    template=couch_template,
                    task_type=task_type,
                    sequence_order=sequence,
                    estimated_duration=duration,
                    description=description,
                    requires_previous_completion=True
                )
        else:
            self.stdout.write(f'  - Template exists: {couch_template.name}')
        
        # Chair Template
        chair_template, created = TaskTemplate.objects.get_or_create(
            name='Standard Chair Production',
            defaults={
                'description': 'Production workflow for chairs and single-seat furniture',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Created template: {chair_template.name}')
            
            # Create template steps for chair (shorter durations)
            chair_steps = [
                (material_prep, 1, timedelta(minutes=30), 'Gather materials for single chair'),
                (cutting, 2, timedelta(minutes=45), 'Cut fabric and foam for chair'),
                (frame_assembly, 3, timedelta(minutes=75), 'Assemble chair frame'),
                (foam_installation, 4, timedelta(minutes=30), 'Install seat and back padding'),
                (upholstery, 5, timedelta(minutes=90), 'Upholster chair'),
                (finishing, 6, timedelta(minutes=45), 'Final finishing work'),
                (quality_check, 7, timedelta(minutes=20), 'Quality inspection'),
                (packaging, 8, timedelta(minutes=15), 'Package chair')
            ]
            
            for task_type, sequence, duration, description in chair_steps:
                TaskTemplateStep.objects.create(
                    template=chair_template,
                    task_type=task_type,
                    sequence_order=sequence,
                    estimated_duration=duration,
                    description=description,
                    requires_previous_completion=True
                )
        else:
            self.stdout.write(f'  - Template exists: {chair_template.name}')
        
        # Custom Order Template
        custom_template, created = TaskTemplate.objects.get_or_create(
            name='Custom Order Production',
            defaults={
                'description': 'Flexible workflow for custom and special orders',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Created template: {custom_template.name}')
            
            # Create template steps for custom orders
            custom_steps = [
                (material_prep, 1, timedelta(minutes=60), 'Prepare custom materials and specifications'),
                (cutting, 2, timedelta(minutes=120), 'Precision cutting for custom dimensions'),
                (frame_assembly, 3, timedelta(minutes=150), 'Custom frame assembly'),
                (foam_installation, 4, timedelta(minutes=90), 'Custom foam work'),
                (upholstery, 5, timedelta(minutes=240), 'Custom upholstery work'),
                (finishing, 6, timedelta(minutes=120), 'Detailed finishing for custom order'),
                (quality_check, 7, timedelta(minutes=45), 'Thorough quality check'),
                (packaging, 8, timedelta(minutes=45), 'Special packaging for custom order')
            ]
            
            for task_type, sequence, duration, description in custom_steps:
                TaskTemplateStep.objects.create(
                    template=custom_template,
                    task_type=task_type,
                    sequence_order=sequence,
                    estimated_duration=duration,
                    description=description,
                    requires_previous_completion=True
                )
        else:
            self.stdout.write(f'  - Template exists: {custom_template.name}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Task setup completed successfully!'))
        self.stdout.write('\nTask types created:')
        for task_type in TaskType.objects.all().order_by('sequence_order'):
            self.stdout.write(f'  • {task_type.name} ({task_type.estimated_duration_minutes} min)')
        
        self.stdout.write('\nTask templates created:')
        for template in TaskTemplate.objects.all():
            step_count = template.steps.count()
            total_time = sum([step.estimated_duration for step in template.steps.all()], timedelta())
            hours = int(total_time.total_seconds() // 3600)
            minutes = int((total_time.total_seconds() % 3600) // 60)
            self.stdout.write(f'  • {template.name} ({step_count} steps, ~{hours}h {minutes}m)')
        
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Create warehouse worker users with role="warehouse"')
        self.stdout.write('2. Use task templates to create tasks for orders')
        self.stdout.write('3. Test task assignment and time tracking features')
        self.stdout.write('4. Set up product-material relationships for automatic material allocation')