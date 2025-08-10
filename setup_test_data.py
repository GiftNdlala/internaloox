#!/usr/bin/env python
"""
Setup test data for warehouse worker role system
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/workspace')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oox_system.settings')
django.setup()

from users.models import User
from tasks.models import TaskType
from orders.models import Order, Customer

def setup_test_data():
    print("Setting up test data for warehouse worker role system...")
    
    # Create test users if they don't exist
    test_users = [
        {'username': 'warehouse_worker1', 'password': 'test123', 'role': 'warehouse_worker', 'first_name': 'Mary', 'last_name': 'Johnson', 'employee_id': 'WW001'},
        {'username': 'warehouse_worker2', 'password': 'test123', 'role': 'warehouse_worker', 'first_name': 'John', 'last_name': 'Smith', 'employee_id': 'WW002'},
        {'username': 'warehouse_manager1', 'password': 'test123', 'role': 'warehouse_manager', 'first_name': 'Tom', 'last_name': 'Wilson', 'employee_id': 'WM001'},
        {'username': 'delivery_user1', 'password': 'test123', 'role': 'delivery', 'first_name': 'Lisa', 'last_name': 'Brown'},
        {'username': 'admin_user1', 'password': 'test123', 'role': 'admin', 'first_name': 'Admin', 'last_name': 'User'},
    ]

    created_users = 0
    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(**user_data)
            print(f'✓ Created user: {user.username} ({user.role})')
            created_users += 1
        else:
            print(f'- User already exists: {user_data["username"]}')

    # Create task types if they don't exist
    task_types = [
        {'name': 'Cutting', 'description': 'Cut materials according to patterns', 'estimated_duration_minutes': 60, 'sequence_order': 1, 'color_code': '#ff6b6b'},
        {'name': 'Upholstery', 'description': 'Upholstery and finishing work', 'estimated_duration_minutes': 180, 'sequence_order': 2, 'color_code': '#4ecdc4'},
        {'name': 'Quality Check', 'description': 'Final quality inspection', 'estimated_duration_minutes': 30, 'sequence_order': 3, 'color_code': '#45b7d1'},
        {'name': 'Assembly', 'description': 'Assemble furniture components', 'estimated_duration_minutes': 90, 'sequence_order': 4, 'color_code': '#95e1d3'},
        {'name': 'Packaging', 'description': 'Package finished products', 'estimated_duration_minutes': 20, 'sequence_order': 5, 'color_code': '#f38ba8'},
    ]

    created_task_types = 0
    for task_type_data in task_types:
        task_type, created = TaskType.objects.get_or_create(name=task_type_data['name'], defaults=task_type_data)
        if created:
            print(f'✓ Created task type: {task_type.name}')
            created_task_types += 1
        else:
            print(f'- Task type already exists: {task_type.name}')

    # Create test customers and orders
    test_customers = [
        {'name': 'John Doe', 'phone': '0801234567', 'email': 'john@example.com', 'address': '123 Main St, City'},
        {'name': 'Jane Smith', 'phone': '0809876543', 'email': 'jane@example.com', 'address': '456 Oak Ave, Town'},
        {'name': 'Bob Johnson', 'phone': '0805555555', 'email': 'bob@example.com', 'address': '789 Pine Rd, Village'},
    ]

    created_customers = 0
    for customer_data in test_customers:
        customer, created = Customer.objects.get_or_create(
            name=customer_data['name'], 
            defaults=customer_data
        )
        if created:
            print(f'✓ Created customer: {customer.name}')
            created_customers += 1

    print(f"\nTest data setup completed!")
    print(f"- Created {created_users} users")
    print(f"- Created {created_task_types} task types")
    print(f"- Created {created_customers} customers")
    
    print(f"\nTest credentials:")
    print(f"- warehouse_worker1 / test123 (Warehouse Worker)")
    print(f"- warehouse_worker2 / test123 (Warehouse Worker)")
    print(f"- warehouse_manager1 / test123 (Warehouse Manager)")
    print(f"- delivery_user1 / test123 (Delivery)")
    print(f"- admin_user1 / test123 (Admin)")

if __name__ == '__main__':
    setup_test_data()