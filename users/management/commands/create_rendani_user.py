from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Create RendaniJerry owner user for production'

    def handle(self, *args, **options):
        username = 'RendaniJerry'
        email = 'RendaniJerry1@gmail.com'
        password = 'RendaniJerry'
        
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User "{username}" already exists')
                )
                # Update existing user
                user = User.objects.get(username=username)
                user.email = email
                user.first_name = 'Rendani'
                user.last_name = 'Jerry'
                user.phone = '0727042740'
                user.role = 'owner'
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated existing user "{username}"')
                )
            else:
                # Create new user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name='Rendani',
                    last_name='Jerry',
                    phone='0727042740',
                    role='owner'
                )
                
                # Set owner permissions
                user.is_staff = True
                user.is_superuser = True
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created new user "{username}"')
                )
            
            # Display user details
            self.stdout.write('\n=== User Details ===')
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Name: {user.first_name} {user.last_name}')
            self.stdout.write(f'Phone: {user.phone}')
            self.stdout.write(f'Role: {user.role}')
            self.stdout.write(f'Is Active: {user.is_active}')
            self.stdout.write(f'Is Staff: {user.is_staff}')
            self.stdout.write(f'Is Superuser: {user.is_superuser}')
            
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 User "{username}" is ready for production!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating user: {str(e)}')
            )
