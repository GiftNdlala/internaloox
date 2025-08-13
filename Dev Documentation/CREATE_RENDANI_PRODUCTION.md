# 🔧 CREATE RENDANI USER IN PRODUCTION

## 📋 Problem
The user `RendaniJerry` exists in local development but not in production database.

## 🚀 Solution Options

### **Option 1: Django Management Command (Recommended)**
Run this command in your production environment:

```bash
python3 manage.py create_rendani_user
```

This will create or update the RendaniJerry user with all correct details.

### **Option 2: Direct API Call (Alternative)**
If you have access to make API calls to your production server:

```bash
curl -X POST https://your-production-domain.com/api/users/create-admin/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "RendaniJerry",
    "password": "RendaniJerry",
    "email": "RendaniJerry1@gmail.com",
    "role": "owner"
  }'
```

### **Option 3: Django Shell (Production)**
If you have shell access to production:

```python
from users.models import User

# Create or update user
user, created = User.objects.get_or_create(
    username='RendaniJerry',
    defaults={
        'email': 'RendaniJerry1@gmail.com',
        'first_name': 'Rendani',
        'last_name': 'Jerry',
        'phone': '0727042740',
        'role': 'owner',
        'is_staff': True,
        'is_superuser': True,
    }
)

# Set password
user.set_password('RendaniJerry')
user.save()

print(f"User {'created' if created else 'updated'}: {user.username}")
```

## ✅ User Details
- **Username:** `RendaniJerry`
- **Password:** `RendaniJerry`
- **Email:** `RendaniJerry1@gmail.com`
- **Phone:** `0727042740`
- **Role:** `owner`
- **Name:** Rendani Jerry

## 🔐 Permissions
- Can access all dashboards (owner, admin, warehouse, delivery)
- Can create and manage other users
- Full system access

## 🧪 Test After Creation
Try logging in with:
- Username: `RendaniJerry`
- Password: `RendaniJerry`

The login should work and return JWT tokens with full owner permissions.
