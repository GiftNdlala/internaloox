# 🚀 CREATE RENDANI USER IN PRODUCTION (No Terminal Access)

## 🎯 **EASIEST SOLUTIONS** (Choose One)

### **Option 1: Direct API Call to Production (RECOMMENDED)**
Use this exact command from your local machine or any computer:

```bash
curl -X POST https://internaloox.onrender.com/api/users/create-admin/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "RendaniJerry",
    "password": "RendaniJerry",
    "email": "RendaniJerry1@gmail.com",
    "role": "owner"
  }'
```

**OR using PowerShell (Windows):**
```powershell
Invoke-RestMethod -Uri "https://internaloox.onrender.com/api/users/create-admin/" -Method POST -ContentType "application/json" -Body '{"username": "RendaniJerry", "password": "RendaniJerry", "email": "RendaniJerry1@gmail.com", "role": "owner"}'
```

### **Option 2: Use Postman or Any API Client**
- **URL:** `https://internaloox.onrender.com/api/users/create-admin/`
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
```json
{
  "username": "RendaniJerry",
  "password": "RendaniJerry",
  "email": "RendaniJerry1@gmail.com",
  "role": "owner"
}
```

### **Option 3: Browser JavaScript Console**
1. Open your browser and go to any website
2. Press `F12` to open Developer Tools
3. Go to the `Console` tab
4. Paste and run this code:

```javascript
fetch('https://internaloox.onrender.com/api/users/create-admin/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'RendaniJerry',
    password: 'RendaniJerry',
    email: 'RendaniJerry1@gmail.com',
    role: 'owner'
  })
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

## ✅ **Expected Success Response:**
```json
{
  "success": true,
  "message": "User RendaniJerry created successfully",
  "user_id": 13
}
```

## ❌ **If User Already Exists:**
```json
{
  "error": "User already exists"
}
```
*This means the user was already created successfully!*

## 🧪 **Test After Creation:**
Try logging in from your frontend with:
- **Username:** `RendaniJerry`
- **Password:** `RendaniJerry`

## 🔐 **User Details Being Created:**
- **Username:** RendaniJerry
- **Password:** RendaniJerry  
- **Email:** RendaniJerry1@gmail.com
- **Role:** owner (full permissions)
