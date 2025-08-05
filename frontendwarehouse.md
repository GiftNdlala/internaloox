# 🏭 Warehouse Dashboard Frontend Implementation Guide

## 🚀 **ENHANCED BACKEND IMPLEMENTATION COMPLETE**

### ✅ **NEW FEATURES IMPLEMENTED**

This document has been updated with all the enhanced backend features that are now **READY FOR FRONTEND INTEGRATION**:

#### **🎯 Enhanced Role System**
- ✅ **New Roles**: `warehouse_manager` and `warehouse_worker` added
- ✅ **Backward Compatibility**: Legacy `warehouse` role still supported
- ✅ **Role Properties**: Added `can_manage_tasks`, `is_warehouse_manager`, etc.
- ✅ **Worker Fields**: Added `employee_id`, `shift_start`, `shift_end`, `is_active_worker`

#### **📋 Enhanced Task Management**
- ✅ **Order-Task Creation**: `/api/orders/{id}/create_task/` endpoint
- ✅ **Bulk Assignment**: `/api/tasks/tasks/bulk_reassign/` endpoint  
- ✅ **Enhanced Actions**: Real-time timer tracking with pause/resume
- ✅ **Task Templates**: Pre-defined workflows for common tasks
- ✅ **Progress Tracking**: Real-time progress percentage and time elapsed

#### **🔔 Real-time Notification System**
- ✅ **Notification Model**: Complete notification system with priority levels
- ✅ **Real-time Updates**: `/api/tasks/dashboard/real_time_updates/` endpoint
- ✅ **Notification Management**: Mark as read, bulk operations
- ✅ **Auto-notifications**: Task assignments, completions, overdue alerts

#### **📦 Enhanced Inventory Integration**
- ✅ **Quick Stock Entry**: Batch stock movement creation
- ✅ **Stock Alerts**: Low stock level notifications
- ✅ **Enhanced Tracking**: Batch numbers, expiry dates, locations

#### **🛡️ Role-based Security**
- ✅ **Permission System**: Role-based access control implemented
- ✅ **Task Permissions**: Only managers can create/assign tasks
- ✅ **Worker Restrictions**: Workers see only their assigned tasks
- ✅ **API Security**: All endpoints protected with proper permissions

### 🔧 **READY FOR FRONTEND**

All backend endpoints are **FULLY IMPLEMENTED** and ready for frontend integration. The enhanced API provides:

- **Complete Order-Task Workflow**: Create tasks within orders, assign to workers
- **Real-time Updates**: Live notifications and task status tracking  
- **Enhanced User Management**: New role system with proper permissions
- **Comprehensive Dashboard Data**: Role-based dashboard endpoints
- **Mobile-Optimized APIs**: Efficient data structures for mobile apps

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [Core Components Architecture](#core-components-architecture)
5. [Order-Task Workflow Implementation](#order-task-workflow-implementation)
6. [Real-time Updates & Polling](#real-time-updates--polling)
7. [State Management Strategy](#state-management-strategy)
8. [UI/UX Guidelines](#uiux-guidelines)
9. [Error Handling](#error-handling)
10. [Testing Strategy](#testing-strategy)
11. [Performance Optimization](#performance-optimization)
12. [Deployment Considerations](#deployment-considerations)

---

## 🎯 System Overview

### Architecture Overview
The warehouse dashboard is built on a **role-based multi-view system** with three primary user types:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OWNER/ADMIN   │    │   SUPERVISOR    │    │ WAREHOUSE WORKER │
│                 │    │                 │    │                 │
│ • All Access    │    │ • Task Assignment│    │ • My Tasks Only │
│ • User Mgmt     │    │ • Progress Track │    │ • Time Tracking │
│ • Reports       │    │ • Approvals     │    │ • Order Context │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Data Flow
```
Orders → Task Assignment → Worker Execution → Progress Tracking → Completion
   ↓           ↓               ↓                 ↓              ↓
 Backend    Frontend        Frontend          Backend       Backend
```

---

## 🔐 Authentication & Authorization

### JWT Token Management
```javascript
// utils/auth.js
export class AuthManager {
  static getToken() {
    return localStorage.getItem('access_token');
  }
  
  static getRefreshToken() {
    return localStorage.getItem('refresh_token');
  }
  
  static async refreshToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token');
    
    const response = await fetch('/api/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      return data.access;
    }
    throw new Error('Token refresh failed');
  }
  
  static getUserRole() {
    const token = this.getToken();
    if (!token) return null;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.role;
    } catch {
      return null;
    }
  }
  
  static canAssignTasks() {
    const role = this.getUserRole();
    return ['owner', 'admin', 'warehouse'].includes(role);
  }
}
```

### API Request Interceptor
```javascript
// utils/api.js
export class ApiClient {
  constructor(baseURL = '/api') {
    this.baseURL = baseURL;
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = AuthManager.getToken();
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };
    
    try {
      let response = await fetch(url, config);
      
      // Handle token expiration
      if (response.status === 401) {
        try {
          const newToken = await AuthManager.refreshToken();
          config.headers['Authorization'] = `Bearer ${newToken}`;
          response = await fetch(url, config);
        } catch {
          // Redirect to login
          window.location.href = '/login';
          return;
        }
      }
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Request failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }
  
  get(endpoint) {
    return this.request(endpoint);
  }
  
  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
  
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
```

---

## 📡 API Endpoints Reference

### 🏢 Order Management Endpoints

#### Get Warehouse Orders
```javascript
// GET /api/orders/warehouse_orders/
const getWarehouseOrders = async () => {
  return await api.get('/orders/warehouse_orders/');
};

/* Response Structure:
{
  "orders": [
    {
      "id": 45,
      "order_number": "OOX000045",
      "customer_name": "John Doe",
      "urgency": "high",
      "days_until_deadline": 3,
      "task_counts": {
        "total": 2,
        "not_started": 1,
        "in_progress": 1,
        "completed": 0
      },
      "items_count": 3,
      "total_amount": 5500.00,
      "delivery_deadline": "2024-12-25",
      "is_priority_order": false
    }
  ],
  "summary": {
    "total_orders": 12,
    "critical": 2,
    "high": 4,
    "medium": 3,
    "low": 3
  }
}
*/
```

#### Get Order Details for Task Assignment
```javascript
// GET /api/orders/{order_id}/order_details_for_tasks/
const getOrderDetailsForTasks = async (orderId) => {
  return await api.get(`/orders/${orderId}/order_details_for_tasks/`);
};

/* Response Structure:
{
  "order": {
    "id": 45,
    "order_number": "OOX000045",
    "customer_name": "John Doe",
    "delivery_deadline": "2024-12-25",
    "total_amount": 5500.00,
    "admin_notes": "Rush order",
    "warehouse_notes": "Handle with care"
  },
  "items": [
    {
      "id": 123,
      "product_name": "L-Shaped Couch",
      "quantity": 1,
      "fabric_name": "Premium Suede",
      "color_name": "Navy Blue",
      "required_materials": [
        {
          "material_id": 1,
          "material_name": "Suede Fabric",
          "quantity_required": 12.5,
          "unit": "Meters",
          "total_needed": 12.5
        }
      ]
    }
  ],
  "existing_tasks": [
    {
      "id": 67,
      "title": "Cutting - Order OOX000045",
      "task_type": "Cutting",
      "assigned_to": "John Smith",
      "assigned_to_id": 5,
      "status": "completed",
      "priority": "high"
    }
  ],
  "task_summary": {
    "total_tasks": 2,
    "completed": 1,
    "in_progress": 1,
    "pending": 0
  }
}
*/
```

#### Assign Tasks to Order
```javascript
// POST /api/orders/{order_id}/assign_tasks_to_order/
const assignTasksToOrder = async (orderId, tasks) => {
  return await api.post(`/orders/${orderId}/assign_tasks_to_order/`, { tasks });
};

/* Request Body Structure:
{
  "tasks": [
    {
      "task_type_id": 2,
      "assigned_to_id": 5,
      "title": "Cutting - Order OOX000045",
      "description": "Cut fabric and foam for L-shaped couch",
      "priority": "high",
      "due_date": "2024-12-22T16:00:00Z",
      "order_item_id": 123,
      "required_materials": [
        {
          "material_id": 1,
          "quantity_needed": 12.5
        }
      ]
    }
  ]
}
*/
```

### 📋 Task Management Endpoints

#### Get Tasks by Order (Worker View)
```javascript
// GET /api/tasks/dashboard/tasks_by_order/
const getTasksByOrder = async () => {
  return await api.get('/tasks/dashboard/tasks_by_order/');
};

/* Response Structure:
{
  "orders_with_tasks": [
    {
      "order_info": {
        "id": 45,
        "order_number": "OOX000045",
        "customer_name": "John Doe",
        "delivery_deadline": "2024-12-25",
        "urgency": "high"
      },
      "tasks": [
        {
          "id": 123,
          "title": "Cutting - Order OOX000045",
          "task_type": "Cutting",
          "status": "assigned",
          "priority": "high",
          "is_running": false,
          "is_overdue": false,
          "time_elapsed_formatted": "0h 0m",
          "total_time_formatted": "0h 0m",
          "can_start": true,
          "can_pause": false,
          "can_complete": false
        }
      ]
    }
  ],
  "summary": {
    "total_orders": 5,
    "total_tasks": 12,
    "active_tasks": 2
  }
}
*/
```

#### Task Actions (Start/Pause/Complete)
```javascript
// POST /api/tasks/tasks/{task_id}/perform_action/
const performTaskAction = async (taskId, action, reason = '') => {
  return await api.post(`/tasks/tasks/${taskId}/perform_action/`, { action, reason });
};

/* Available Actions:
- "start": Start working on task
- "pause": Pause current work
- "resume": Resume paused task
- "complete": Mark task as completed
- "approve": Approve completed task (supervisors only)
- "reject": Reject completed task (supervisors only)
*/
```

#### Get Orders with Tasks (Supervisor View)
```javascript
// GET /api/tasks/dashboard/orders_with_tasks/
const getOrdersWithTasks = async () => {
  return await api.get('/tasks/dashboard/orders_with_tasks/');
};

/* Response Structure:
{
  "orders_by_status": {
    "no_tasks": [...],      // Orders without assigned tasks
    "in_progress": [...],   // Orders with active tasks
    "completed": [...],     // Orders with all tasks completed
    "mixed_status": [...]   // Orders with mixed task statuses
  },
  "summary": {
    "no_tasks": 3,
    "in_progress": 5,
    "completed": 2,
    "mixed_status": 1,
    "total_orders": 11
  }
}
*/
```

#### 🔥 NEW: Create Task in Order
```javascript
// POST /api/orders/{order_id}/create_task/
const createTaskInOrder = async (orderId, taskData) => {
  return await api.post(`/orders/${orderId}/create_task/`, taskData);
};

/* Request Body:
{
  "title": "Cut fabric pieces",
  "description": "Cut fabric for L-shaped couch",
  "task_type_id": 1,
  "assigned_to_id": 5,
  "priority": "high",
  "estimated_duration": 120,  // minutes
  "deadline": "2024-12-25T15:00:00Z",
  "instructions": "Follow the pattern carefully",
  "materials_needed": "Suede fabric, cutting tools"
}
*/

/* Response:
{
  "message": "Task created successfully",
  "task": {
    "id": 156,
    "title": "Cut fabric pieces",
    "task_type": "Cutting",
    "assigned_to": "Mary Johnson",
    "status": "assigned",
    "priority": "high",
    "order": 45,
    "deadline": "2024-12-25T15:00:00Z"
  }
}
*/
```

#### 🔥 NEW: Bulk Task Assignment  
```javascript
// POST /api/tasks/tasks/bulk_reassign/
const bulkAssignTasks = async (taskIds, workerId) => {
  return await api.post('/tasks/tasks/bulk_reassign/', {
    task_ids: taskIds,
    worker_id: workerId
  });
};

/* Request Body:
{
  "task_ids": [123, 124, 125],
  "worker_id": 5
}
*/

/* Response:
{
  "message": "3 tasks assigned successfully",
  "assigned_count": 3
}
*/
```

#### 🔥 NEW: Real-time Updates
```javascript
// GET /api/tasks/dashboard/real_time_updates/?since=timestamp
const getRealTimeUpdates = async (since = null) => {
  const url = since ? `/tasks/dashboard/real_time_updates/?since=${since}` : '/tasks/dashboard/real_time_updates/';
  return await api.get(url);
};

/* Response Structure:
{
  "has_updates": true,
  "notifications": [
    {
      "id": 45,
      "message": "New task assigned: Cut fabric pieces",
      "type": "task_assigned",
      "priority": "normal",
      "is_read": false,
      "created_at": "2024-12-16T14:30:00Z",
      "task_id": 156,
      "order_id": 45
    }
  ],
  "task_updates": [
    {
      "id": 123,
      "title": "Upholstery work",
      "status": "started",
      "assigned_to": "John Smith",
      "order_number": "OOX000045",
      "is_running": true,
      "updated_at": "2024-12-16T14:25:00Z"
    }
  ],
  "stock_alerts": [
    {
      "id": 12,
      "name": "Premium Suede",
      "current_stock": 5.2,
      "minimum_stock_level": 10.0,
      "unit": "Meters"
    }
  ],
  "timestamp": "2024-12-16T14:35:00Z"
}
*/
```

#### 🔥 NEW: Enhanced Task Actions
```javascript
// POST /api/tasks/tasks/{task_id}/perform_action/
const performEnhancedTaskAction = async (taskId, action, reason = '') => {
  return await api.post(`/tasks/tasks/${taskId}/perform_action/`, { action, reason });
};

/* Enhanced Response:
{
  "message": "Task started successfully",
  "task_status": "started",
  "task_id": 123,
  "is_running": true,
  "time_elapsed": 0,
  "progress_percentage": 0,
  "can_start": false,
  "can_pause": true,
  "can_resume": false,
  "can_complete": true
}
*/
```

### 🔔 Notification Management Endpoints

#### Get User Notifications
```javascript
// GET /api/tasks/notifications/
const getUserNotifications = async () => {
  return await api.get('/tasks/notifications/');
};
```

#### Mark All Notifications as Read
```javascript
// POST /api/tasks/notifications/mark_all_read/
const markAllNotificationsRead = async () => {
  return await api.post('/tasks/notifications/mark_all_read/');
};

/* Response:
{
  "message": "5 notifications marked as read",
  "updated_count": 5
}
*/
```

#### Mark Single Notification as Read
```javascript
// POST /api/tasks/notifications/{id}/mark_read/
const markNotificationRead = async (notificationId) => {
  return await api.post(`/tasks/notifications/${notificationId}/mark_read/`);
};
```

### 📦 Enhanced Inventory Endpoints

#### 🔥 NEW: Quick Stock Entry (Batch)
```javascript
// POST /api/inventory/materials/quick_stock_entry/
const quickStockEntry = async (entries) => {
  return await api.post('/inventory/materials/quick_stock_entry/', { entries });
};

/* Request Body:
{
  "entries": [
    {
      "material_id": 12,
      "movement_type": "in",
      "quantity": 50.0,
      "reason": "New delivery",
      "location": "Warehouse A",
      "batch_number": "BATCH001",
      "expiry_date": "2025-12-31"
    },
    {
      "material_id": 15,
      "movement_type": "out", 
      "quantity": 5.5,
      "reason": "Used for Order OOX000045",
      "location": "Production Floor"
    }
  ]
}
*/

/* Response:
{
  "message": "2 stock movements created",
  "movements": [
    {
      "movement_id": 456,
      "material_name": "Premium Suede",
      "movement_type": "in",
      "quantity": 50.0,
      "new_stock_level": 55.2,
      "status": "success"
    }
  ],
  "success_count": 2,
  "error_count": 0
}
*/
```

### 🎯 Task Types & Templates

#### Get Task Types
```javascript
// GET /api/tasks/task-types/
const getTaskTypes = async () => {
  return await api.get('/tasks/task-types/');
};

/* Response:
[
  {
    "id": 1,
    "name": "Cutting",
    "description": "Cut materials according to patterns",
    "estimated_duration_minutes": 60,
    "requires_materials": true,
    "color_code": "#ff6b6b",
    "is_active": true,
    "sequence_order": 1
  }
]
*/
```

#### Get Task Templates
```javascript
// GET /api/tasks/templates/
const getTaskTemplates = async () => {
  return await api.get('/tasks/templates/');
};

/* Response:
[
  {
    "id": 1,
    "name": "Standard Couch Production",
    "description": "Complete production workflow for couches",
    "task_type": "Production",
    "priority": "normal",
    "estimated_duration": 480,
    "instructions": "Follow standard production guidelines",
    "materials_needed": "Fabric, foam, springs, wood frame",
    "is_active": true
  }
]
*/
```

### 👥 User Management (Enhanced Roles)

#### Get Warehouse Workers
```javascript
// GET /api/users/warehouse_workers/
const getWarehouseWorkers = async () => {
  return await api.get('/users/warehouse_workers/');
};

/* Response:
[
  {
    "id": 5,
    "username": "mary_johnson",
    "first_name": "Mary",
    "last_name": "Johnson", 
    "email": "mary@oox.com",
    "role": "warehouse_worker",
    "employee_id": "WW001",
    "shift_start": "08:00:00",
    "shift_end": "17:00:00",
    "is_active_worker": true,
    "can_manage_tasks": false
  },
  {
    "id": 6,
    "username": "supervisor_tom",
    "first_name": "Tom",
    "last_name": "Wilson",
    "email": "tom@oox.com", 
    "role": "warehouse_manager",
    "employee_id": "WM001",
    "can_manage_tasks": true
  }
]
*/
```

### 📊 Dashboard Endpoints

#### Worker Dashboard
```javascript
// GET /api/tasks/dashboard/worker_dashboard/
const getWorkerDashboard = async () => {
  return await api.get('/tasks/dashboard/worker_dashboard/');
};
```

#### Supervisor Dashboard
```javascript
// GET /api/tasks/dashboard/supervisor_dashboard/
const getSupervisorDashboard = async () => {
  return await api.get('/tasks/dashboard/supervisor_dashboard/');
};
```

#### Real-time Updates
```javascript
// GET /api/tasks/dashboard/real_time_updates/
const getRealTimeUpdates = async () => {
  return await api.get('/tasks/dashboard/real_time_updates/');
};
```

### 📦 Inventory Endpoints

#### Warehouse Dashboard
```javascript
// GET /api/inventory/materials/warehouse_dashboard/
const getInventoryDashboard = async () => {
  return await api.get('/inventory/materials/warehouse_dashboard/');
};
```

#### Quick Stock Entry
```javascript
// POST /api/inventory/materials/quick_stock_entry/
const addQuickStock = async (stockData) => {
  return await api.post('/inventory/materials/quick_stock_entry/', stockData);
};
```

---

## 🏗️ Core Components Architecture

### 1. Route Structure
```javascript
// App.js
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected Routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            {/* Worker Routes */}
            <Route path="worker-dashboard" element={<WorkerDashboard />} />
            <Route path="my-tasks-by-order" element={<WorkerOrderTasks />} />
            <Route path="my-tasks" element={<WorkerTasks />} />
            
            {/* Supervisor Routes */}
            <Route path="supervisor-dashboard" element={<SupervisorDashboard />} />
            <Route path="orders-today" element={<WarehouseOrders />} />
            <Route path="orders/:id/assign-tasks" element={<OrderTaskAssignment />} />
            <Route path="orders/:id/progress" element={<OrderProgress />} />
            
            {/* Inventory Routes */}
            <Route path="inventory" element={<InventoryDashboard />} />
            <Route path="stock-entry" element={<StockEntry />} />
            
            {/* Admin Routes */}
            <Route path="admin-dashboard" element={<AdminDashboard />} />
            <Route path="reports" element={<Reports />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}
```

### 2. Context Providers

#### Auth Context
```javascript
// contexts/AuthContext.js
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { AuthManager } from '../utils/auth';

const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        role: action.payload.role,
        loading: false,
      };
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        role: null,
        loading: false,
      };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, {
    isAuthenticated: false,
    user: null,
    role: null,
    loading: true,
  });

  useEffect(() => {
    const token = AuthManager.getToken();
    const role = AuthManager.getUserRole();
    
    if (token && role) {
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user: { role }, role },
      });
    } else {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const login = async (credentials) => {
    try {
      const response = await api.post('/token/', credentials);
      
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      const role = AuthManager.getUserRole();
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user: { role }, role },
      });
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    dispatch({ type: 'LOGOUT' });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

#### Warehouse Context
```javascript
// contexts/WarehouseContext.js
import React, { createContext, useContext, useReducer } from 'react';

const WarehouseContext = createContext();

const warehouseReducer = (state, action) => {
  switch (action.type) {
    case 'SET_ORDERS':
      return { ...state, orders: action.payload };
    case 'SET_TASKS':
      return { ...state, tasks: action.payload };
    case 'UPDATE_TASK':
      return {
        ...state,
        tasks: state.tasks.map(task =>
          task.id === action.payload.id ? { ...task, ...action.payload } : task
        ),
      };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    default:
      return state;
  }
};

export const WarehouseProvider = ({ children }) => {
  const [state, dispatch] = useReducer(warehouseReducer, {
    orders: [],
    tasks: [],
    loading: false,
    error: null,
  });

  const setOrders = (orders) => {
    dispatch({ type: 'SET_ORDERS', payload: orders });
  };

  const setTasks = (tasks) => {
    dispatch({ type: 'SET_TASKS', payload: tasks });
  };

  const updateTask = (taskUpdate) => {
    dispatch({ type: 'UPDATE_TASK', payload: taskUpdate });
  };

  const setLoading = (loading) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };

  const setError = (error) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  };

  return (
    <WarehouseContext.Provider value={{
      ...state,
      setOrders,
      setTasks,
      updateTask,
      setLoading,
      setError,
    }}>
      {children}
    </WarehouseContext.Provider>
  );
};

export const useWarehouse = () => {
  const context = useContext(WarehouseContext);
  if (!context) {
    throw new Error('useWarehouse must be used within a WarehouseProvider');
  }
  return context;
};
```

### 3. Custom Hooks

#### useTaskActions Hook
```javascript
// hooks/useTaskActions.js
import { useState } from 'react';
import { api } from '../utils/api';
import { useWarehouse } from '../contexts/WarehouseContext';

export const useTaskActions = () => {
  const [loading, setLoading] = useState(false);
  const { updateTask } = useWarehouse();

  const performAction = async (taskId, action, reason = '') => {
    setLoading(true);
    try {
      const result = await api.post(`/tasks/tasks/${taskId}/perform_action/`, {
        action,
        reason,
      });

      // Update local state
      updateTask({
        id: taskId,
        status: result.new_status,
        is_running: result.is_running,
        time_elapsed: result.time_elapsed,
      });

      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  };

  const startTask = (taskId) => performAction(taskId, 'start');
  const pauseTask = (taskId) => performAction(taskId, 'pause');
  const resumeTask = (taskId) => performAction(taskId, 'resume');
  const completeTask = (taskId, reason) => performAction(taskId, 'complete', reason);

  return {
    loading,
    startTask,
    pauseTask,
    resumeTask,
    completeTask,
    performAction,
  };
};
```

#### usePolling Hook
```javascript
// hooks/usePolling.js
import { useEffect, useRef, useState } from 'react';

export const usePolling = (fetchFunction, interval = 30000, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef();

  const fetchData = async () => {
    try {
      const result = await fetchFunction();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(); // Initial fetch

    intervalRef.current = setInterval(fetchData, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, dependencies);

  const refresh = () => {
    setLoading(true);
    fetchData();
  };

  return { data, loading, error, refresh };
};
```

---

## 🔄 Order-Task Workflow Implementation

### 1. Warehouse Orders Component
```javascript
// components/WarehouseOrders.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { usePolling } from '../hooks/usePolling';

const WarehouseOrders = () => {
  const navigate = useNavigate();
  const { data, loading, error, refresh } = usePolling(
    () => api.get('/orders/warehouse_orders/'),
    30000 // Refresh every 30 seconds
  );

  const getUrgencyColor = (urgency) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-green-100 text-green-800 border-green-200',
    };
    return colors[urgency] || colors.low;
  };

  const handleOrderClick = (orderId) => {
    navigate(`/orders/${orderId}/assign-tasks`);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading orders</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <button 
              onClick={refresh}
              className="mt-2 text-sm bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { orders = [], summary = {} } = data || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Orders for Today</h1>
        <button 
          onClick={refresh}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="text-sm font-medium text-gray-500">Total Orders</h3>
          <p className="text-2xl font-bold text-gray-900">{summary.total_orders}</p>
        </div>
        <div className="bg-red-50 p-4 rounded-lg shadow border border-red-200">
          <h3 className="text-sm font-medium text-red-600">Critical</h3>
          <p className="text-2xl font-bold text-red-900">{summary.critical}</p>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg shadow border border-orange-200">
          <h3 className="text-sm font-medium text-orange-600">High</h3>
          <p className="text-2xl font-bold text-orange-900">{summary.high}</p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg shadow border border-yellow-200">
          <h3 className="text-sm font-medium text-yellow-600">Medium</h3>
          <p className="text-2xl font-bold text-yellow-900">{summary.medium}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg shadow border border-green-200">
          <h3 className="text-sm font-medium text-green-600">Low</h3>
          <p className="text-2xl font-bold text-green-900">{summary.low}</p>
        </div>
      </div>

      {/* Orders List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {orders.map((order) => (
          <div
            key={order.id}
            className="bg-white rounded-lg shadow-md border hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => handleOrderClick(order.id)}
          >
            <div className="p-6">
              {/* Order Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {order.order_number}
                  </h3>
                  <p className="text-sm text-gray-600">{order.customer_name}</p>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getUrgencyColor(order.urgency)}`}>
                  {order.urgency.toUpperCase()}
                </span>
              </div>

              {/* Order Details */}
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Items:</span>
                  <span className="font-medium">{order.items_count}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Amount:</span>
                  <span className="font-medium">${order.total_amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Deadline:</span>
                  <span className="font-medium">
                    {order.days_until_deadline} days
                  </span>
                </div>
              </div>

              {/* Task Summary */}
              <div className="border-t pt-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Tasks</span>
                  <span className="text-sm text-gray-500">
                    {order.task_counts.completed}/{order.task_counts.total}
                  </span>
                </div>
                
                {order.task_counts.total > 0 ? (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-gray-600">
                      <span>Progress</span>
                      <span>
                        {Math.round((order.task_counts.completed / order.task_counts.total) * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(order.task_counts.completed / order.task_counts.total) * 100}%`
                        }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>In Progress: {order.task_counts.in_progress}</span>
                      <span>Pending: {order.task_counts.not_started}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-2">
                    <span className="text-sm text-gray-500">No tasks assigned</span>
                    <div className="mt-1">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Click to assign tasks
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {orders.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">No orders found</div>
          <p className="text-gray-500">All orders are either completed or not ready for warehouse processing.</p>
        </div>
      )}
    </div>
  );
};

export default WarehouseOrders;
```

### 2. Order Task Assignment Component
```javascript
// components/OrderTaskAssignment.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const OrderTaskAssignment = () => {
  const { id: orderId } = useParams();
  const navigate = useNavigate();
  
  const [orderDetails, setOrderDetails] = useState(null);
  const [taskTypes, setTaskTypes] = useState([]);
  const [availableWorkers, setAvailableWorkers] = useState([]);
  const [tasksToAssign, setTasksToAssign] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, [orderId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [orderResponse, taskTypesResponse, workersResponse] = await Promise.all([
        api.get(`/orders/${orderId}/order_details_for_tasks/`),
        api.get('/tasks/task-types/'),
        api.get('/users/?role=warehouse'),
      ]);

      setOrderDetails(orderResponse);
      setTaskTypes(taskTypesResponse.results || taskTypesResponse);
      setAvailableWorkers(workersResponse.results || workersResponse);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addTask = () => {
    setTasksToAssign([...tasksToAssign, {
      task_type_id: '',
      assigned_to_id: '',
      title: '',
      description: '',
      priority: 'normal',
      due_date: '',
      order_item_id: null,
    }]);
  };

  const updateTask = (index, field, value) => {
    const updated = [...tasksToAssign];
    updated[index][field] = value;
    
    // Auto-generate title if task type or order info changes
    if (field === 'task_type_id' && value) {
      const taskType = taskTypes.find(t => t.id === parseInt(value));
      if (taskType && orderDetails) {
        updated[index].title = `${taskType.name} - ${orderDetails.order.order_number}`;
        updated[index].description = `${taskType.name} for order ${orderDetails.order.order_number}`;
      }
    }
    
    setTasksToAssign(updated);
  };

  const removeTask = (index) => {
    setTasksToAssign(tasksToAssign.filter((_, i) => i !== index));
  };

  const assignTasks = async () => {
    if (tasksToAssign.length === 0) {
      setError('Please add at least one task');
      return;
    }

    // Validate tasks
    const invalidTasks = tasksToAssign.filter(
      task => !task.task_type_id || !task.assigned_to_id || !task.title
    );

    if (invalidTasks.length > 0) {
      setError('Please fill in all required fields for each task');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const result = await api.post(`/orders/${orderId}/assign_tasks_to_order/`, {
        tasks: tasksToAssign,
      });

      // Show success message
      alert(`${result.created_tasks.length} tasks assigned successfully!`);
      
      // Navigate back to orders list
      navigate('/orders-today');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error && !orderDetails) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-red-800">Error loading order details</h3>
        <p className="mt-1 text-sm text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Assign Tasks - {orderDetails?.order.order_number}
          </h1>
          <p className="text-gray-600">
            Customer: {orderDetails?.order.customer_name} | 
            Deadline: {orderDetails?.order.delivery_deadline}
          </p>
        </div>
        <button
          onClick={() => navigate('/orders-today')}
          className="text-gray-600 hover:text-gray-800"
        >
          ← Back to Orders
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Order Details */}
        <div className="space-y-6">
          {/* Order Items */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Order Items</h2>
            <div className="space-y-4">
              {orderDetails?.items.map((item, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium">{item.product_name}</h3>
                    <span className="text-sm text-gray-500">Qty: {item.quantity}</span>
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>Fabric: {item.fabric_name}</p>
                    <p>Color: {item.color_name}</p>
                    <p>Price: ${item.unit_price}</p>
                  </div>
                  
                  {item.required_materials.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Required Materials:</h4>
                      <div className="space-y-1">
                        {item.required_materials.map((material, idx) => (
                          <div key={idx} className="text-xs text-gray-600 flex justify-between">
                            <span>{material.material_name}</span>
                            <span>{material.total_needed} {material.unit}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Existing Tasks */}
          {orderDetails?.existing_tasks.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                Existing Tasks ({orderDetails.task_summary.total_tasks})
              </h2>
              <div className="space-y-3">
                {orderDetails.existing_tasks.map((task) => (
                  <div key={task.id} className="flex justify-between items-center p-3 border rounded">
                    <div>
                      <h3 className="font-medium">{task.title}</h3>
                      <p className="text-sm text-gray-600">
                        {task.task_type} - Assigned to: {task.assigned_to}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      task.status === 'completed' ? 'bg-green-100 text-green-800' :
                      task.status === 'started' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {task.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Task Assignment */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Assign New Tasks</h2>
            <button
              onClick={addTask}
              className="bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700"
            >
              + Add Task
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            {tasksToAssign.map((task, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium">Task {index + 1}</h3>
                  <button
                    onClick={() => removeTask(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-3">
                  {/* Task Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Task Type *
                    </label>
                    <select
                      value={task.task_type_id}
                      onChange={(e) => updateTask(index, 'task_type_id', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select Task Type</option>
                      {taskTypes.map((type) => (
                        <option key={type.id} value={type.id}>
                          {type.name} ({type.estimated_duration_minutes}min)
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Assigned Worker */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Assign to Worker *
                    </label>
                    <select
                      value={task.assigned_to_id}
                      onChange={(e) => updateTask(index, 'assigned_to_id', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select Worker</option>
                      {availableWorkers.map((worker) => (
                        <option key={worker.id} value={worker.id}>
                          {worker.first_name} {worker.last_name} ({worker.username})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Task Title */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Task Title *
                    </label>
                    <input
                      type="text"
                      value={task.title}
                      onChange={(e) => updateTask(index, 'title', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Task title"
                      required
                    />
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={task.description}
                      onChange={(e) => updateTask(index, 'description', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows="2"
                      placeholder="Task description"
                    />
                  </div>

                  {/* Priority & Due Date */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Priority
                      </label>
                      <select
                        value={task.priority}
                        onChange={(e) => updateTask(index, 'priority', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="low">Low</option>
                        <option value="normal">Normal</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Due Date
                      </label>
                      <input
                        type="datetime-local"
                        value={task.due_date}
                        onChange={(e) => updateTask(index, 'due_date', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {tasksToAssign.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>No tasks added yet.</p>
                <p className="text-sm">Click "Add Task" to start assigning tasks to this order.</p>
              </div>
            )}
          </div>

          {tasksToAssign.length > 0 && (
            <div className="mt-6 pt-4 border-t">
              <button
                onClick={assignTasks}
                disabled={submitting}
                className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Assigning Tasks...' : `Assign ${tasksToAssign.length} Task${tasksToAssign.length > 1 ? 's' : ''}`}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrderTaskAssignment;
```

### 3. Worker Order Tasks Component
```javascript
// components/WorkerOrderTasks.js
import React, { useState } from 'react';
import { usePolling } from '../hooks/usePolling';
import { useTaskActions } from '../hooks/useTaskActions';
import { api } from '../utils/api';

const WorkerOrderTasks = () => {
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const { data, loading, error, refresh } = usePolling(
    () => api.get('/tasks/dashboard/tasks_by_order/'),
    15000 // Refresh every 15 seconds for workers
  );

  const {
    loading: actionLoading,
    startTask,
    pauseTask,
    resumeTask,
    completeTask,
  } = useTaskActions();

  const handleTaskAction = async (taskId, action) => {
    let result;
    switch (action) {
      case 'start':
        result = await startTask(taskId);
        break;
      case 'pause':
        result = await pauseTask(taskId);
        break;
      case 'resume':
        result = await resumeTask(taskId);
        break;
      case 'complete':
        const reason = prompt('Add completion notes (optional):');
        result = await completeTask(taskId, reason || '');
        break;
      default:
        return;
    }

    if (result.success) {
      refresh(); // Refresh the data
    } else {
      alert(`Error: ${result.error}`);
    }
  };

  const getUrgencyColor = (urgency) => {
    const colors = {
      critical: 'border-red-500 bg-red-50',
      high: 'border-orange-500 bg-orange-50',
      medium: 'border-yellow-500 bg-yellow-50',
      low: 'border-green-500 bg-green-50',
    };
    return colors[urgency] || colors.low;
  };

  const getStatusColor = (status) => {
    const colors = {
      assigned: 'bg-gray-100 text-gray-800',
      started: 'bg-blue-100 text-blue-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      approved: 'bg-green-100 text-green-800',
    };
    return colors[status] || colors.assigned;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-red-800">Error loading tasks</h3>
        <p className="mt-1 text-sm text-red-700">{error}</p>
        <button 
          onClick={refresh}
          className="mt-2 text-sm bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    );
  }

  const { orders_with_tasks = [], summary = {} } = data || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Tasks by Order</h1>
          <p className="text-gray-600">
            {summary.total_orders} orders • {summary.total_tasks} tasks • {summary.active_tasks} active
          </p>
        </div>
        <button 
          onClick={refresh}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Orders with Tasks */}
      <div className="space-y-6">
        {orders_with_tasks.map((orderGroup) => (
          <div
            key={orderGroup.order_info.id}
            className={`border-l-4 rounded-lg shadow-md bg-white ${getUrgencyColor(orderGroup.order_info.urgency)}`}
          >
            {/* Order Header */}
            <div 
              className="p-4 cursor-pointer"
              onClick={() => setSelectedOrderId(
                selectedOrderId === orderGroup.order_info.id ? null : orderGroup.order_info.id
              )}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {orderGroup.order_info.order_number}
                  </h2>
                  <p className="text-gray-600">{orderGroup.order_info.customer_name}</p>
                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                    <span>Deadline: {orderGroup.order_info.delivery_deadline}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      orderGroup.order_info.urgency === 'critical' ? 'bg-red-100 text-red-800' :
                      orderGroup.order_info.urgency === 'high' ? 'bg-orange-100 text-orange-800' :
                      orderGroup.order_info.urgency === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {orderGroup.order_info.urgency.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">
                    {orderGroup.tasks.length} task{orderGroup.tasks.length !== 1 ? 's' : ''}
                  </div>
                  <div className="text-xs text-gray-400">
                    {selectedOrderId === orderGroup.order_info.id ? '▼' : '▶'} Click to {selectedOrderId === orderGroup.order_info.id ? 'collapse' : 'expand'}
                  </div>
                </div>
              </div>
            </div>

            {/* Tasks List */}
            {selectedOrderId === orderGroup.order_info.id && (
              <div className="border-t bg-gray-50">
                <div className="p-4 space-y-4">
                  {orderGroup.tasks.map((task) => (
                    <div
                      key={task.id}
                      className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">{task.title}</h3>
                          <p className="text-sm text-gray-600">{task.task_type}</p>
                          {task.is_overdue && (
                            <p className="text-sm text-red-600 font-medium">⚠️ Overdue</p>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(task.status)}`}>
                          {task.status}
                        </span>
                      </div>

                      {/* Time Tracking */}
                      {(task.is_running || task.total_time_formatted !== '0h 0m') && (
                        <div className="mb-3 p-2 bg-blue-50 rounded text-sm">
                          <div className="flex justify-between">
                            <span>Time Spent:</span>
                            <span className="font-medium">{task.total_time_formatted}</span>
                          </div>
                          {task.is_running && (
                            <div className="flex justify-between text-blue-600">
                              <span>Current Session:</span>
                              <span className="font-medium">{task.time_elapsed_formatted}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Task Actions */}
                      <div className="flex space-x-2">
                        {task.can_start && (
                          <button
                            onClick={() => handleTaskAction(task.id, 'start')}
                            disabled={actionLoading}
                            className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                          >
                            ▶️ Start
                          </button>
                        )}
                        
                        {task.status === 'started' && (
                          <button
                            onClick={() => handleTaskAction(task.id, 'pause')}
                            disabled={actionLoading}
                            className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700 disabled:opacity-50"
                          >
                            ⏸️ Pause
                          </button>
                        )}
                        
                        {task.status === 'paused' && (
                          <button
                            onClick={() => handleTaskAction(task.id, 'resume')}
                            disabled={actionLoading}
                            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                          >
                            ▶️ Resume
                          </button>
                        )}
                        
                        {task.can_complete && (
                          <button
                            onClick={() => handleTaskAction(task.id, 'complete')}
                            disabled={actionLoading}
                            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                          >
                            ✅ Complete
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {orders_with_tasks.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">No tasks assigned</div>
          <p className="text-gray-500">You don't have any tasks assigned to you at the moment.</p>
        </div>
      )}
    </div>
  );
};

export default WorkerOrderTasks;
```

---

## ⚡ Real-time Updates & Polling

### Polling Strategy
```javascript
// hooks/useRealTimeUpdates.js
import { useState, useEffect, useRef } from 'react';
import { api } from '../utils/api';

export const useRealTimeUpdates = (interval = 30000) => {
  const [updates, setUpdates] = useState({
    notifications: [],
    task_updates: [],
    stock_alerts: [],
  });
  const [lastCheck, setLastCheck] = useState(null);
  const intervalRef = useRef();

  const fetchUpdates = async () => {
    try {
      const params = lastCheck ? `?since=${lastCheck}` : '';
      const response = await api.get(`/tasks/dashboard/real_time_updates/${params}`);
      
      if (response.has_updates) {
        setUpdates(response);
        
        // Show notifications for critical updates
        response.notifications.forEach(notification => {
          if (notification.priority === 'high') {
            showNotification(notification.message);
          }
        });
      }
      
      setLastCheck(new Date().toISOString());
    } catch (error) {
      console.error('Error fetching real-time updates:', error);
    }
  };

  const showNotification = (message) => {
    if (Notification.permission === 'granted') {
      new Notification('OOX Warehouse', {
        body: message,
        icon: '/favicon.ico',
      });
    }
  };

  useEffect(() => {
    // Request notification permission
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    fetchUpdates(); // Initial fetch
    intervalRef.current = setInterval(fetchUpdates, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [interval]);

  return { updates, refresh: fetchUpdates };
};
```

### Notification Component
```javascript
// components/NotificationBell.js
import React, { useState } from 'react';
import { useRealTimeUpdates } from '../hooks/useRealTimeUpdates';

const NotificationBell = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { updates } = useRealTimeUpdates();
  
  const unreadCount = updates.notifications.filter(n => !n.is_read).length;

  const markAsRead = async (notificationId) => {
    try {
      await api.post(`/tasks/notifications/${notificationId}/mark_read/`);
      // Update local state
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-800"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19H6.5A2.5 2.5 0 014 16.5v-7A2.5 2.5 0 016.5 7H18a2 2 0 012 2v7a2 2 0 01-2 2h-1" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border z-50">
          <div className="p-4 border-b">
            <h3 className="text-lg font-semibold">Notifications</h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {updates.notifications.length > 0 ? (
              updates.notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b hover:bg-gray-50 ${!notification.is_read ? 'bg-blue-50' : ''}`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!notification.is_read && (
                      <div className="w-2 h-2 bg-blue-500 rounded-full ml-2"></div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-gray-500">
                No notifications
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
```

---

## 🎨 UI/UX Guidelines

### Color Scheme
```css
/* styles/colors.css */
:root {
  /* Primary Colors */
  --primary-50: #eff6ff;
  --primary-100: #dbeafe;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  --primary-700: #1d4ed8;

  /* Status Colors */
  --success-50: #f0fdf4;
  --success-100: #dcfce7;
  --success-500: #22c55e;
  --success-600: #16a34a;

  --warning-50: #fffbeb;
  --warning-100: #fef3c7;
  --warning-500: #f59e0b;
  --warning-600: #d97706;

  --error-50: #fef2f2;
  --error-100: #fee2e2;
  --error-500: #ef4444;
  --error-600: #dc2626;

  /* Urgency Colors */
  --critical: #dc2626;
  --high: #ea580c;
  --medium: #ca8a04;
  --low: #16a34a;

  /* Neutral Colors */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-500: #6b7280;
  --gray-600: #4b5563;
  --gray-900: #111827;
}
```

### Status Indicators
```javascript
// utils/statusUtils.js
export const getStatusConfig = (status) => {
  const configs = {
    // Task Statuses
    assigned: {
      color: 'bg-gray-100 text-gray-800',
      icon: '📋',
      label: 'Assigned'
    },
    started: {
      color: 'bg-blue-100 text-blue-800',
      icon: '▶️',
      label: 'In Progress'
    },
    paused: {
      color: 'bg-yellow-100 text-yellow-800',
      icon: '⏸️',
      label: 'Paused'
    },
    completed: {
      color: 'bg-green-100 text-green-800',
      icon: '✅',
      label: 'Completed'
    },
    approved: {
      color: 'bg-green-100 text-green-800',
      icon: '✅',
      label: 'Approved'
    },
    rejected: {
      color: 'bg-red-100 text-red-800',
      icon: '❌',
      label: 'Rejected'
    },

    // Urgency Levels
    critical: {
      color: 'bg-red-100 text-red-800 border-red-200',
      icon: '🚨',
      label: 'Critical'
    },
    high: {
      color: 'bg-orange-100 text-orange-800 border-orange-200',
      icon: '⚠️',
      label: 'High'
    },
    medium: {
      color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      icon: '⚡',
      label: 'Medium'
    },
    low: {
      color: 'bg-green-100 text-green-800 border-green-200',
      icon: '🟢',
      label: 'Low'
    }
  };

  return configs[status] || configs.assigned;
};

export const StatusBadge = ({ status, showIcon = true }) => {
  const config = getStatusConfig(status);
  
  return (
    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
      {showIcon && <span className="mr-1">{config.icon}</span>}
      {config.label}
    </span>
  );
};
```

### Responsive Design
```css
/* styles/responsive.css */
.dashboard-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1280px) {
  .dashboard-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* Mobile-first task cards */
.task-card {
  @apply bg-white rounded-lg shadow border p-4;
}

@media (max-width: 640px) {
  .task-card {
    @apply p-3;
  }
  
  .task-actions {
    @apply flex-col space-y-2;
  }
  
  .task-actions button {
    @apply w-full;
  }
}
```

---

## 🛡️ Error Handling

### Global Error Handler
```javascript
// utils/errorHandler.js
export class ErrorHandler {
  static handle(error, context = '') {
    console.error(`Error in ${context}:`, error);
    
    let userMessage = 'An unexpected error occurred';
    
    if (error.message) {
      // API errors
      if (error.message.includes('401')) {
        userMessage = 'Session expired. Please log in again.';
        // Redirect to login
        window.location.href = '/login';
        return;
      } else if (error.message.includes('403')) {
        userMessage = 'You do not have permission to perform this action.';
      } else if (error.message.includes('404')) {
        userMessage = 'The requested resource was not found.';
      } else if (error.message.includes('500')) {
        userMessage = 'Server error. Please try again later.';
      } else {
        userMessage = error.message;
      }
    }
    
    // Show user-friendly error
    this.showError(userMessage);
    
    // Log to monitoring service (if available)
    this.logError(error, context);
  }
  
  static showError(message) {
    // You can integrate with toast libraries like react-hot-toast
    alert(message); // Simple fallback
  }
  
  static logError(error, context) {
    // Send to monitoring service like Sentry
    console.error('Logged error:', { error, context, timestamp: new Date().toISOString() });
  }
}
```

### Error Boundary Component
```javascript
// components/ErrorBoundary.js
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900">Something went wrong</h3>
              <p className="mt-2 text-sm text-gray-500">
                An error occurred while loading this page. Please refresh and try again.
              </p>
              <div className="mt-6">
                <button
                  onClick={() => window.location.reload()}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Refresh Page
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

---

## 🧪 Testing Strategy

### Unit Tests Example
```javascript
// __tests__/utils/auth.test.js
import { AuthManager } from '../../utils/auth';

describe('AuthManager', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('should return null when no token exists', () => {
    expect(AuthManager.getToken()).toBeNull();
  });

  test('should return token when it exists', () => {
    const token = 'test-token';
    localStorage.setItem('access_token', token);
    expect(AuthManager.getToken()).toBe(token);
  });

  test('should extract role from valid JWT token', () => {
    // Mock JWT token with role: 'warehouse'
    const mockToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoid2FyZWhvdXNlIn0.signature';
    localStorage.setItem('access_token', mockToken);
    
    expect(AuthManager.getUserRole()).toBe('warehouse');
  });

  test('should return correct permissions for roles', () => {
    // Test owner permissions
    jest.spyOn(AuthManager, 'getUserRole').mockReturnValue('owner');
    expect(AuthManager.canAssignTasks()).toBe(true);

    // Test warehouse worker permissions  
    jest.spyOn(AuthManager, 'getUserRole').mockReturnValue('warehouse');
    expect(AuthManager.canAssignTasks()).toBe(true);

    // Test delivery permissions
    jest.spyOn(AuthManager, 'getUserRole').mockReturnValue('delivery');
    expect(AuthManager.canAssignTasks()).toBe(false);
  });
});
```

### Component Tests Example
```javascript
// __tests__/components/WorkerOrderTasks.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import WorkerOrderTasks from '../../components/WorkerOrderTasks';
import { api } from '../../utils/api';

// Mock the API
jest.mock('../../utils/api');

const mockData = {
  orders_with_tasks: [
    {
      order_info: {
        id: 1,
        order_number: 'OOX000001',
        customer_name: 'John Doe',
        urgency: 'high'
      },
      tasks: [
        {
          id: 1,
          title: 'Cutting - Order OOX000001',
          task_type: 'Cutting',
          status: 'assigned',
          can_start: true,
          can_pause: false,
          can_complete: false
        }
      ]
    }
  ],
  summary: {
    total_orders: 1,
    total_tasks: 1,
    active_tasks: 0
  }
};

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('WorkerOrderTasks', () => {
  beforeEach(() => {
    api.get.mockResolvedValue(mockData);
  });

  test('renders order tasks correctly', async () => {
    renderWithRouter(<WorkerOrderTasks />);
    
    await waitFor(() => {
      expect(screen.getByText('My Tasks by Order')).toBeInTheDocument();
      expect(screen.getByText('OOX000001')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Cutting - Order OOX000001')).toBeInTheDocument();
    });
  });

  test('handles task start action', async () => {
    const user = userEvent.setup();
    api.post.mockResolvedValue({ success: true, new_status: 'started' });
    
    renderWithRouter(<WorkerOrderTasks />);
    
    await waitFor(() => {
      expect(screen.getByText('▶️ Start')).toBeInTheDocument();
    });
    
    await user.click(screen.getByText('▶️ Start'));
    
    expect(api.post).toHaveBeenCalledWith('/tasks/tasks/1/perform_action/', {
      action: 'start',
      reason: ''
    });
  });

  test('shows loading state', () => {
    api.get.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    renderWithRouter(<WorkerOrderTasks />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  test('handles API errors gracefully', async () => {
    api.get.mockRejectedValue(new Error('Network error'));
    
    renderWithRouter(<WorkerOrderTasks />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading tasks')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });
});
```

### Integration Tests
```javascript
// __tests__/integration/taskWorkflow.test.js
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';
import { api } from '../../utils/api';

jest.mock('../../utils/api');

describe('Task Workflow Integration', () => {
  test('complete task assignment workflow', async () => {
    const user = userEvent.setup();
    
    // Mock API responses
    api.get.mockImplementation((endpoint) => {
      if (endpoint === '/orders/warehouse_orders/') {
        return Promise.resolve({
          orders: [{ id: 1, order_number: 'OOX000001', task_counts: { total: 0 } }],
          summary: { total_orders: 1 }
        });
      }
      if (endpoint === '/orders/1/order_details_for_tasks/') {
        return Promise.resolve({
          order: { id: 1, order_number: 'OOX000001' },
          items: [],
          existing_tasks: []
        });
      }
      if (endpoint === '/tasks/task-types/') {
        return Promise.resolve([{ id: 1, name: 'Cutting' }]);
      }
      if (endpoint === '/users/?role=warehouse') {
        return Promise.resolve([{ id: 1, first_name: 'John', last_name: 'Doe' }]);
      }
    });
    
    api.post.mockResolvedValue({
      created_tasks: [{ task_id: 1, title: 'Cutting - Order OOX000001' }]
    });
    
    render(<BrowserRouter><App /></BrowserRouter>);
    
    // Navigate to orders
    await user.click(screen.getByText('Orders Today'));
    
    // Click on order
    await waitFor(() => {
      expect(screen.getByText('OOX000001')).toBeInTheDocument();
    });
    await user.click(screen.getByText('OOX000001'));
    
    // Add task
    await user.click(screen.getByText('+ Add Task'));
    
    // Fill task form
    await user.selectOptions(screen.getByLabelText('Task Type *'), '1');
    await user.selectOptions(screen.getByLabelText('Assign to Worker *'), '1');
    await user.type(screen.getByLabelText('Task Title *'), 'Cutting - Order OOX000001');
    
    // Submit
    await user.click(screen.getByText('Assign 1 Task'));
    
    // Verify API call
    expect(api.post).toHaveBeenCalledWith('/orders/1/assign_tasks_to_order/', {
      tasks: expect.arrayContaining([
        expect.objectContaining({
          task_type_id: '1',
          assigned_to_id: '1',
          title: 'Cutting - Order OOX000001'
        })
      ])
    });
  });
});
```

---

## 🚀 Performance Optimization

### Code Splitting
```javascript
// App.js with lazy loading
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoadingSpinner from './components/LoadingSpinner';

// Lazy load components
const WorkerDashboard = React.lazy(() => import('./components/WorkerDashboard'));
const SupervisorDashboard = React.lazy(() => import('./components/SupervisorDashboard'));
const WarehouseOrders = React.lazy(() => import('./components/WarehouseOrders'));
const OrderTaskAssignment = React.lazy(() => import('./components/OrderTaskAssignment'));

function App() {
  return (
    <Router>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/worker-dashboard" element={<WorkerDashboard />} />
          <Route path="/supervisor-dashboard" element={<SupervisorDashboard />} />
          <Route path="/orders-today" element={<WarehouseOrders />} />
          <Route path="/orders/:id/assign-tasks" element={<OrderTaskAssignment />} />
        </Routes>
      </Suspense>
    </Router>
  );
}
```

### Memoization
```javascript
// components/optimized/TaskCard.js
import React, { memo } from 'react';

const TaskCard = memo(({ task, onAction }) => {
  const handleAction = (action) => {
    onAction(task.id, action);
  };

  return (
    <div className="task-card">
      <h3>{task.title}</h3>
      <p>{task.status}</p>
      {task.can_start && (
        <button onClick={() => handleAction('start')}>
          Start
        </button>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function
  return (
    prevProps.task.id === nextProps.task.id &&
    prevProps.task.status === nextProps.task.status &&
    prevProps.task.is_running === nextProps.task.is_running
  );
});

export default TaskCard;
```

### Virtual Scrolling for Large Lists
```javascript
// components/VirtualizedTaskList.js
import React from 'react';
import { FixedSizeList as List } from 'react-window';

const TaskRow = ({ index, style, data }) => (
  <div style={style}>
    <TaskCard task={data[index]} />
  </div>
);

const VirtualizedTaskList = ({ tasks }) => (
  <List
    height={600}
    itemCount={tasks.length}
    itemSize={120}
    itemData={tasks}
  >
    {TaskRow}
  </List>
);

export default VirtualizedTaskList;
```

---

## 📦 Deployment Considerations

### Environment Configuration
```javascript
// config/environment.js
const config = {
  development: {
    API_BASE_URL: 'http://localhost:8000',
    POLLING_INTERVAL: 5000, // 5 seconds for development
    DEBUG: true,
  },
  production: {
    API_BASE_URL: 'https://api.ooxwarehouse.com',
    POLLING_INTERVAL: 30000, // 30 seconds for production
    DEBUG: false,
  },
};

export default config[process.env.NODE_ENV || 'development'];
```

### Build Optimization
```json
// package.json
{
  "scripts": {
    "build": "npm run build:css && react-scripts build",
    "build:css": "tailwindcss build -i src/styles/tailwind.css -o src/styles/output.css",
    "analyze": "npm run build && npx bundle-analyzer build/static/js/*.js"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ]
  }
}
```

### Service Worker for Offline Support
```javascript
// public/sw.js
const CACHE_NAME = 'oox-warehouse-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});
```

---

## 📋 Implementation Checklist

### Phase 1: Core Setup ✅
- [ ] Set up React app with routing
- [ ] Implement authentication system
- [ ] Create API client with token management
- [ ] Set up context providers
- [ ] Implement error handling

### Phase 2: Order-Task Workflow 🚧
- [ ] Build WarehouseOrders component
- [ ] Create OrderTaskAssignment component
- [ ] Implement WorkerOrderTasks component
- [ ] Add task action handlers
- [ ] Test complete workflow

### Phase 3: Real-time Features 📋
- [ ] Implement polling system
- [ ] Add notification bell
- [ ] Create real-time updates
- [ ] Add browser notifications
- [ ] Test performance impact

### Phase 4: UI/UX Polish 📋
- [ ] Apply consistent styling
- [ ] Add loading states
- [ ] Implement responsive design
- [ ] Add animations/transitions
- [ ] Test accessibility

### Phase 5: Testing & Optimization 📋
- [ ] Write unit tests
- [ ] Add integration tests
- [ ] Implement code splitting
- [ ] Add performance monitoring
- [ ] Optimize bundle size

### Phase 6: Deployment 📋
- [ ] Set up build pipeline
- [ ] Configure environment variables
- [ ] Add service worker
- [ ] Test production build
- [ ] Deploy to staging/production

---

## 🆘 Troubleshooting

### Common Issues

#### 1. Token Expiration
**Problem**: Users getting logged out unexpectedly
**Solution**: Check token refresh logic in `AuthManager.refreshToken()`

#### 2. Polling Performance
**Problem**: Too many API calls affecting performance
**Solution**: Adjust polling intervals and implement smart polling

#### 3. Real-time Updates Not Working
**Problem**: Workers not seeing task updates
**Solution**: Verify polling is running and check network tab for failed requests

#### 4. Task Actions Failing
**Problem**: Start/pause/complete actions not working
**Solution**: Check user permissions and task status validation

#### 5. Mobile Layout Issues
**Problem**: Components not responsive on mobile
**Solution**: Review CSS media queries and test on actual devices

---

## 📞 Support & Resources

### Documentation Links
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Router](https://reactrouter.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

### Team Contacts
- **Backend Team**: For API issues and database queries
- **DevOps Team**: For deployment and environment issues
- **Design Team**: For UI/UX guidelines and assets

---

*This guide covers the complete implementation of the OOX Warehouse Dashboard frontend. Follow the phases sequentially and refer to the troubleshooting section for common issues. Update this document as the system evolves.*