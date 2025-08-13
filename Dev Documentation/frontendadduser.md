# 🔧 Frontend User Management Integration Guide

## 📋 Overview
Complete guide for integrating user management (Create, Read, Update, Delete) functionality with the backend API. This guide ensures proper connection to the Supabase users_user table through Django REST endpoints.

---

## 🚀 API Endpoints Summary

| Operation | Method | Endpoint | Description |
|-----------|---------|----------|-------------|
| **List Users** | GET | `/api/users/users/` | Get all users (with pagination) |
| **Get User** | GET | `/api/users/users/{id}/` | Get specific user details |
| **Create User** | POST | `/api/users/users/` | Create new user |
| **Update User** | PUT/PATCH | `/api/users/users/{id}/` | Update existing user |
| **Delete User** | DELETE | `/api/users/users/{id}/` | Delete user |

**Base URL:** `https://internaloox.onrender.com`

---

## 🔐 Authentication Requirements

**ALL endpoints require JWT Bearer token authentication:**

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}`
};
```

**Permission Requirements:**
- **List Users:** Owner can see all, Admin can see all except owners, Others see only themselves
- **Create User:** Only Owner role
- **Update User:** Only Owner role  
- **Delete User:** Only Owner role
- **Get User:** Based on visibility rules

---

## 📊 1. LIST USERS

### **GET /api/users/users/**

**Purpose:** Retrieve all users with pagination support

**Headers:**
```javascript
{
  'Authorization': 'Bearer {access_token}',
  'Content-Type': 'application/json'
}
```

**Response Format:**
```json
{
  "success": true,
  "count": 25,
  "next": "http://localhost:8000/api/users/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "admin",
      "role_display": "Admin",
      "phone": "+1234567890",
      "is_active": true,
      "last_login": "2025-07-22T10:30:00Z",
      "date_joined": "2025-07-20T09:15:00Z"
    }
  ],
  "total_users": 25,
  "user_role": "owner"
}
```

**Frontend Implementation:**
```javascript
const fetchUsers = async (page = 1) => {
  try {
    const response = await fetch(`${BASE_URL}/api/users/users/?page=${page}`, {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      return {
        users: data.results,
        totalUsers: data.total_users,
        hasNext: !!data.next,
        hasPrevious: !!data.previous,
        userRole: data.user_role
      };
    } else {
      throw new Error(data.error || 'Failed to fetch users');
    }
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};
```

---

## 👤 2. GET SINGLE USER

### **GET /api/users/users/{id}/**

**Purpose:** Get detailed information about a specific user

**Response Format:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "admin",
    "role_display": "Admin",
    "phone": "+1234567890",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "last_login": "2025-07-22T10:30:00Z",
    "date_joined": "2025-07-20T09:15:00Z"
  }
}
```

**Frontend Implementation:**
```javascript
const fetchUser = async (userId) => {
  try {
    const response = await fetch(`${BASE_URL}/api/users/users/${userId}/`, {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      return data.user;
    } else {
      throw new Error(data.error || 'Failed to fetch user');
    }
  } catch (error) {
    console.error('Error fetching user:', error);
    throw error;
  }
};
```

---

## ➕ 3. CREATE USER

### **POST /api/users/users/**

**Purpose:** Create a new user (Owner only)

**Request Body:**
```json
{
  "username": "new_user",
  "password": "securePassword123",
  "password_confirm": "securePassword123",
  "email": "newuser@example.com",
  "first_name": "New",
  "last_name": "User",
  "role": "admin",
  "phone": "+1234567890"
}
```

**Field Requirements:**
- ✅ **Required:** `username`, `password`, `password_confirm`
- ✅ **Optional:** `email`, `first_name`, `last_name`, `role`, `phone`
- ✅ **Role Options:** `owner`, `admin`, `warehouse`, `delivery`
- ✅ **Password Rules:** Must pass Django's password validation

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "User \"new_user\" created successfully",
  "user": {
    "id": 15,
    "username": "new_user",
    "email": "newuser@example.com",
    "first_name": "New",
    "last_name": "User",
    "role": "admin",
    "role_display": "Admin",
    "phone": "+1234567890",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "last_login": null,
    "date_joined": "2025-07-22T15:30:00Z"
  }
}
```

**Error Responses:**

**403 Forbidden (Non-owner user):**
```json
{
  "error": "Only users with Owner role can create new users",
  "required_role": "owner",
  "your_role": "admin"
}
```

**400 Bad Request (Validation errors):**
```json
{
  "password": ["This password is too short. It must contain at least 8 characters."],
  "password_confirm": ["Passwords do not match."],
  "username": ["A user with that username already exists."]
}
```

**Frontend Implementation:**
```javascript
const createUser = async (userData) => {
  try {
    const response = await fetch(`${BASE_URL}/api/users/users/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showSuccess(data.message);
      return data.user;
    } else {
      // Handle validation errors
      if (response.status === 400) {
        handleValidationErrors(data);
      } else if (response.status === 403) {
        showError(`Access denied: ${data.error}`);
      } else {
        showError(data.error || 'Failed to create user');
      }
      throw new Error(data.error || 'Failed to create user');
    }
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

// Helper function for validation errors
const handleValidationErrors = (errorData) => {
  Object.keys(errorData).forEach(field => {
    const errors = Array.isArray(errorData[field]) ? errorData[field] : [errorData[field]];
    errors.forEach(error => {
      showFieldError(field, error);
    });
  });
};
```

---

## ✏️ 4. UPDATE USER

### **PUT /api/users/users/{id}/** or **PATCH /api/users/users/{id}/**

**Purpose:** Update existing user (Owner only)

**Request Body (PATCH - partial update):**
```json
{
  "first_name": "Updated",
  "last_name": "Name",
  "role": "warehouse"
}
```

**Request Body (PUT - full update):**
```json
{
  "username": "updated_user",
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "User",
  "role": "warehouse",
  "phone": "+1234567890",
  "is_active": true
}
```

**Password Update (optional):**
```json
{
  "password": "newPassword123",
  "password_confirm": "newPassword123",
  "first_name": "Updated Name"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "User \"updated_user\" updated successfully",
  "user": {
    "id": 15,
    "username": "updated_user",
    "email": "updated@example.com",
    "first_name": "Updated",
    "last_name": "User",
    "role": "warehouse",
    "role_display": "Warehouse",
    "phone": "+1234567890",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "last_login": null,
    "date_joined": "2025-07-22T15:30:00Z"
  }
}
```

**Frontend Implementation:**
```javascript
const updateUser = async (userId, userData, isPartialUpdate = true) => {
  try {
    const method = isPartialUpdate ? 'PATCH' : 'PUT';
    
    const response = await fetch(`${BASE_URL}/api/users/users/${userId}/`, {
      method: method,
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showSuccess(data.message);
      return data.user;
    } else {
      if (response.status === 400) {
        handleValidationErrors(data);
      } else if (response.status === 403) {
        showError(`Access denied: ${data.error}`);
      } else {
        showError(data.error || 'Failed to update user');
      }
      throw new Error(data.error || 'Failed to update user');
    }
  } catch (error) {
    console.error('Error updating user:', error);
    throw error;
  }
};
```

---

## 🗑️ 5. DELETE USER

### **DELETE /api/users/users/{id}/**

**Purpose:** Delete a user (Owner only)

**Success Response (204 No Content):**
```json
{
  "success": true,
  "message": "User \"username\" deleted successfully"
}
```

**Error Responses:**

**400 Bad Request (Self-deletion attempt):**
```json
{
  "error": "You cannot delete your own account",
  "suggestion": "Ask another owner to delete your account if needed"
}
```

**403 Forbidden:**
```json
{
  "error": "Only users with Owner role can delete users",
  "required_role": "owner",
  "your_role": "admin"
}
```

**Frontend Implementation:**
```javascript
const deleteUser = async (userId, username) => {
  try {
    // Confirmation dialog
    const confirmed = await showConfirmDialog(
      `Are you sure you want to delete user "${username}"?`,
      'This action cannot be undone.'
    );
    
    if (!confirmed) return false;
    
    const response = await fetch(`${BASE_URL}/api/users/users/${userId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showSuccess(data.message);
      return true;
    } else {
      if (response.status === 400) {
        showError(data.error, data.suggestion);
      } else if (response.status === 403) {
        showError(`Access denied: ${data.error}`);
      } else {
        showError(data.error || 'Failed to delete user');
      }
      throw new Error(data.error || 'Failed to delete user');
    }
  } catch (error) {
    console.error('Error deleting user:', error);
    throw error;
  }
};
```

---

## 🎨 Frontend Components Examples

### **User Management Component**
```javascript
import React, { useState, useEffect } from 'react';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  useEffect(() => {
    loadUsers();
  }, [currentPage]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const result = await fetchUsers(currentPage);
      setUsers(result.users);
      setTotalUsers(result.totalUsers);
    } catch (error) {
      showError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (userData) => {
    try {
      await createUser(userData);
      setShowCreateModal(false);
      loadUsers(); // Refresh list
    } catch (error) {
      // Error handling is done in createUser function
    }
  };

  const handleUpdateUser = async (userId, userData) => {
    try {
      await updateUser(userId, userData);
      setEditingUser(null);
      loadUsers(); // Refresh list
    } catch (error) {
      // Error handling is done in updateUser function
    }
  };

  const handleDeleteUser = async (userId, username) => {
    try {
      const deleted = await deleteUser(userId, username);
      if (deleted) {
        loadUsers(); // Refresh list
      }
    } catch (error) {
      // Error handling is done in deleteUser function
    }
  };

  return (
    <div className="user-management">
      <div className="header">
        <h2>User Management</h2>
        <button onClick={() => setShowCreateModal(true)}>
          Add New User
        </button>
      </div>

      {loading ? (
        <div>Loading users...</div>
      ) : (
        <>
          <UserTable 
            users={users}
            onEdit={setEditingUser}
            onDelete={handleDeleteUser}
          />
          
          <Pagination 
            currentPage={currentPage}
            totalItems={totalUsers}
            onPageChange={setCurrentPage}
          />
        </>
      )}

      {showCreateModal && (
        <CreateUserModal 
          onSubmit={handleCreateUser}
          onClose={() => setShowCreateModal(false)}
        />
      )}

      {editingUser && (
        <EditUserModal 
          user={editingUser}
          onSubmit={(userData) => handleUpdateUser(editingUser.id, userData)}
          onClose={() => setEditingUser(null)}
        />
      )}
    </div>
  );
};
```

### **Create User Form**
```javascript
const CreateUserForm = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    password_confirm: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'delivery',
    phone: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      await onSubmit(formData);
      // Reset form on success
      setFormData({
        username: '',
        password: '',
        password_confirm: '',
        email: '',
        first_name: '',
        last_name: '',
        role: 'delivery',
        phone: ''
      });
    } catch (error) {
      // Errors are handled by the parent component
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="create-user-form">
      <div className="form-group">
        <label>Username *</label>
        <input
          type="text"
          name="username"
          value={formData.username}
          onChange={handleChange}
          required
          className={errors.username ? 'error' : ''}
        />
        {errors.username && <span className="error-text">{errors.username}</span>}
      </div>

      <div className="form-group">
        <label>Password *</label>
        <input
          type="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          required
          className={errors.password ? 'error' : ''}
        />
        {errors.password && <span className="error-text">{errors.password}</span>}
      </div>

      <div className="form-group">
        <label>Confirm Password *</label>
        <input
          type="password"
          name="password_confirm"
          value={formData.password_confirm}
          onChange={handleChange}
          required
          className={errors.password_confirm ? 'error' : ''}
        />
        {errors.password_confirm && <span className="error-text">{errors.password_confirm}</span>}
      </div>

      <div className="form-group">
        <label>Email</label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          className={errors.email ? 'error' : ''}
        />
        {errors.email && <span className="error-text">{errors.email}</span>}
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>First Name</label>
          <input
            type="text"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label>Last Name</label>
          <input
            type="text"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
          />
        </div>
      </div>

      <div className="form-group">
        <label>Role</label>
        <select
          name="role"
          value={formData.role}
          onChange={handleChange}
          className={errors.role ? 'error' : ''}
        >
          <option value="delivery">Delivery</option>
          <option value="warehouse">Warehouse</option>
          <option value="admin">Admin</option>
          <option value="owner">Owner</option>
        </select>
        {errors.role && <span className="error-text">{errors.role}</span>}
      </div>

      <div className="form-group">
        <label>Phone</label>
        <input
          type="tel"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="+1234567890"
        />
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create User'}
        </button>
      </div>
    </form>
  );
};
```

---

## 🚨 Error Handling

### **Common Error Scenarios:**

**1. Authentication Errors (401):**
```javascript
if (response.status === 401) {
  // Token expired or invalid
  redirectToLogin();
  return;
}
```

**2. Permission Errors (403):**
```javascript
if (response.status === 403) {
  showError('You do not have permission to perform this action');
  return;
}
```

**3. Validation Errors (400):**
```javascript
if (response.status === 400) {
  const data = await response.json();
  // Handle field-specific validation errors
  handleValidationErrors(data);
  return;
}
```

**4. Not Found Errors (404):**
```javascript
if (response.status === 404) {
  showError('User not found');
  return;
}
```

**5. Server Errors (500):**
```javascript
if (response.status >= 500) {
  showError('Server error. Please try again later.');
  return;
}
```

---

## 🛡️ Security Best Practices

### **1. Token Management:**
```javascript
// Store tokens securely
const storeTokens = (accessToken, refreshToken) => {
  // Use httpOnly cookies or secure storage
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
};

// Auto-refresh tokens
const getAccessToken = async () => {
  let token = localStorage.getItem('access_token');
  
  // Check if token is expired and refresh if needed
  if (isTokenExpired(token)) {
    token = await refreshAccessToken();
  }
  
  return token;
};
```

### **2. Input Validation:**
```javascript
const validateUserForm = (formData) => {
  const errors = {};
  
  if (!formData.username || formData.username.length < 3) {
    errors.username = 'Username must be at least 3 characters';
  }
  
  if (!formData.password || formData.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }
  
  if (formData.password !== formData.password_confirm) {
    errors.password_confirm = 'Passwords do not match';
  }
  
  if (formData.email && !isValidEmail(formData.email)) {
    errors.email = 'Please enter a valid email address';
  }
  
  return errors;
};
```

### **3. Permission Checks:**
```javascript
const canPerformAction = (userRole, action) => {
  const permissions = {
    'owner': ['create', 'read', 'update', 'delete'],
    'admin': ['read'],
    'warehouse': ['read'],
    'delivery': ['read']
  };
  
  return permissions[userRole]?.includes(action) || false;
};
```

---

## 🧪 Testing Checklist

### **Frontend Testing:**
- [ ] ✅ List users with pagination
- [ ] ✅ Search and filter users
- [ ] ✅ Create user with all fields
- [ ] ✅ Create user with minimal fields
- [ ] ✅ Update user information
- [ ] ✅ Update user password
- [ ] ✅ Delete user with confirmation
- [ ] ✅ Handle validation errors
- [ ] ✅ Handle permission errors
- [ ] ✅ Handle network errors
- [ ] ✅ Role-based UI visibility
- [ ] ✅ Token refresh handling

### **Backend Integration:**
- [ ] ✅ All CRUD operations work
- [ ] ✅ Data persists to Supabase users_user table
- [ ] ✅ Role-based permissions enforced
- [ ] ✅ Password validation working
- [ ] ✅ Email uniqueness enforced
- [ ] ✅ Username uniqueness enforced
- [ ] ✅ Owner permissions auto-set

---

## 📱 Mobile Considerations

### **Responsive Design:**
```css
/* Mobile-first approach */
.user-management {
  padding: 1rem;
}

@media (min-width: 768px) {
  .user-management {
    padding: 2rem;
  }
  
  .form-row {
    display: flex;
    gap: 1rem;
  }
}
```

### **Touch-Friendly Interactions:**
```javascript
// Larger touch targets for mobile
const buttonStyles = {
  minHeight: '44px', // iOS recommendation
  minWidth: '44px',
  padding: '12px 16px'
};
```

---

## 🔄 State Management

### **Redux/Context Example:**
```javascript
// User management actions
const userActions = {
  FETCH_USERS_START: 'FETCH_USERS_START',
  FETCH_USERS_SUCCESS: 'FETCH_USERS_SUCCESS',
  FETCH_USERS_ERROR: 'FETCH_USERS_ERROR',
  CREATE_USER_SUCCESS: 'CREATE_USER_SUCCESS',
  UPDATE_USER_SUCCESS: 'UPDATE_USER_SUCCESS',
  DELETE_USER_SUCCESS: 'DELETE_USER_SUCCESS'
};

// User reducer
const userReducer = (state = initialState, action) => {
  switch (action.type) {
    case userActions.FETCH_USERS_SUCCESS:
      return {
        ...state,
        users: action.payload.users,
        totalUsers: action.payload.totalUsers,
        loading: false
      };
    
    case userActions.CREATE_USER_SUCCESS:
      return {
        ...state,
        users: [action.payload, ...state.users],
        totalUsers: state.totalUsers + 1
      };
    
    case userActions.UPDATE_USER_SUCCESS:
      return {
        ...state,
        users: state.users.map(user => 
          user.id === action.payload.id ? action.payload : user
        )
      };
    
    case userActions.DELETE_USER_SUCCESS:
      return {
        ...state,
        users: state.users.filter(user => user.id !== action.payload.id),
        totalUsers: state.totalUsers - 1
      };
    
    default:
      return state;
  }
};
```

---

## 🎯 Summary

### **Key Points:**
1. **Use `/api/users/users/` endpoints** (NOT `/api/users/create/`)
2. **Only Owner role** can create, update, delete users
3. **All endpoints require JWT authentication**
4. **Password confirmation required** for creation/updates
5. **Comprehensive error handling** for all scenarios
6. **Role-based UI visibility** for better UX
7. **Data persists directly to Supabase** users_user table

### **Ready for Implementation:**
✅ **All CRUD operations tested and working**  
✅ **Comprehensive error handling implemented**  
✅ **Role-based permissions enforced**  
✅ **Frontend examples provided**  
✅ **Security best practices included**  
✅ **Mobile considerations addressed**  

**Your frontend team can now implement full user management functionality!** 🚀

---

*Last updated: July 22, 2025*  
*Version: 1.0*  
*Backend API Version: Django 4.2.7 + DRF*
