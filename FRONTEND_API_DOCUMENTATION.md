# 🚀 OOX Warehouse Dashboard - Frontend API Documentation

## Overview

This document provides comprehensive API documentation for the frontend team to integrate with the warehouse management system. All endpoints require authentication via JWT tokens.

## 🔐 Authentication

All API requests require a Bearer token in the Authorization header:
```javascript
headers: {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
}
```

## 📊 Dashboard Endpoints

### 1. Warehouse Worker Dashboard
**GET** `/api/tasks/dashboard/worker_dashboard/`

Returns complete dashboard data for warehouse workers.

**Response:**
```json
{
  "worker_info": {
    "name": "John Doe",
    "role": "Warehouse",
    "username": "john_doe"
  },
  "task_summary": {
    "total_tasks": 15,
    "assigned": 3,
    "in_progress": 1,
    "completed_today": 2,
    "overdue": 0
  },
  "active_task": {
    "id": 123,
    "title": "Upholstery - Order OOX000045",
    "status": "started",
    "time_elapsed_formatted": "1h 30m"
  },
  "active_session": {
    "id": 456,
    "started_at": "2024-12-20T10:30:00Z",
    "duration_formatted": "1h 30m"
  },
  "recent_tasks": [...],
  "notifications": [...],
  "today_productivity": {...}
}
```

### 2. Supervisor Dashboard
**GET** `/api/tasks/dashboard/supervisor_dashboard/`

Returns dashboard data for supervisors (admin, owner, warehouse managers).

**Response:**
```json
{
  "overview": {
    "total_tasks": 45,
    "assigned": 12,
    "in_progress": 8,
    "completed": 20,
    "overdue": 5,
    "total_workers": 6
  },
  "worker_status": [
    {
      "worker_id": 1,
      "worker_name": "John Doe",
      "total_tasks": 8,
      "active_task": {...},
      "completed_today": 2,
      "overdue_tasks": 0
    }
  ],
  "recent_activities": [...],
  "tasks_for_approval": [...],
  "overdue_tasks": [...]
}
```

### 3. Inventory Dashboard
**GET** `/api/inventory/materials/warehouse_dashboard/`

Returns complete inventory dashboard data.

**Response:**
```json
{
  "overview": {
    "total_materials": 50,
    "low_stock_count": 8,
    "critical_stock_count": 3,
    "total_inventory_value": 45000.00,
    "active_alerts_count": 5
  },
  "stock_status": {
    "optimal": 39,
    "low": 5,
    "critical": 3
  },
  "low_stock_materials": [...],
  "critical_stock_materials": [...],
  "recent_movements": [...],
  "active_alerts": [...],
  "materials_by_category": {...},
  "top_suppliers": [...]
}
```

## 📋 Task Management Endpoints

### 1. Get My Tasks (Worker View)
**GET** `/api/tasks/tasks/my_tasks/`

Returns tasks assigned to the current user.

### 2. Task Actions (Start, Pause, Complete)
**POST** `/api/tasks/tasks/{task_id}/action/`

**Request Body:**
```json
{
  "action": "start",  // start, pause, resume, complete, approve, reject
  "reason": "Optional reason for pause/reject"
}
```

**Response:**
```json
{
  "message": "Task started successfully",
  "task_status": "started",
  "task_id": 123
}
```

### 3. Quick Task Assignment (Supervisors)
**POST** `/api/tasks/dashboard/quick_task_assign/`

**Request Body:**
```json
{
  "assigned_to": 1,
  "task_type": 2,
  "title": "Upholstery work for Order OOX000123",
  "description": "Apply fabric covering to couch frame",
  "priority": "normal",
  "due_date": "2024-12-25T16:00:00Z",
  "order_id": 45
}
```

### 4. Task Assignment Data
**GET** `/api/tasks/dashboard/task_assignment_data/`

Returns data needed for task assignment interface (workers, task types, orders, templates).

### 5. Real-time Updates
**GET** `/api/tasks/dashboard/real_time_updates/?last_check=2024-12-20T10:00:00Z`

Returns new notifications, task updates, and stock alerts since last check.

## 📦 Inventory Management Endpoints

### 1. Materials List
**GET** `/api/inventory/materials/`

**Query Parameters:**
- `stock_status`: `low`, `critical`, `optimal`
- `category`: Filter by material category
- `search`: Search in name/description

### 2. Stock Entry (Quick)
**POST** `/api/inventory/materials/quick_stock_entry/`

**Request Body:**
```json
{
  "entries": [
    {
      "material_id": 1,
      "quantity": 50,
      "reason": "Monthly restock",
      "unit_cost": 45.00,
      "location": "Section A-001"
    }
  ]
}
```

### 3. Stock Locations
**GET** `/api/inventory/materials/stock_locations/`

Returns materials with their storage locations.

### 4. Low Stock Materials
**GET** `/api/inventory/materials/low_stock/`

### 5. Update Material Stock
**POST** `/api/inventory/materials/{material_id}/update_stock/`

**Request Body:**
```json
{
  "new_stock": 75.5,
  "reason": "Stock adjustment",
  "unit_cost": 45.00
}
```

## 👥 User Management Integration

### 1. Current User Info
**GET** `/api/users/me/`

Returns current user information with role and permissions.

### 2. Warehouse Workers List
**GET** `/api/users/?role=warehouse`

Returns list of warehouse workers for task assignment.

## 🔔 Notifications

### 1. Unread Notifications
**GET** `/api/tasks/notifications/unread/`

### 2. Mark Notification as Read
**POST** `/api/tasks/notifications/{notification_id}/mark_read/`

### 3. Mark All Notifications as Read
**POST** `/api/tasks/notifications/mark_all_read/`

## 📈 Reporting Endpoints

### 1. Material Usage Report
**GET** `/api/inventory/predictions/reports/?type=usage`

### 2. Low Stock Report
**GET** `/api/inventory/predictions/reports/?type=low_stock`

### 3. Worker Productivity Report
**GET** `/api/tasks/productivity/summary_report/?start_date=2024-12-01&end_date=2024-12-20`

## 🎨 Frontend Integration Examples

### React Hook for Dashboard Data
```javascript
import { useState, useEffect } from 'react';

export const useWarehouseDashboard = (userRole) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      const token = localStorage.getItem('access_token');
      const endpoint = userRole === 'warehouse' 
        ? '/api/tasks/dashboard/worker_dashboard/'
        : '/api/tasks/dashboard/supervisor_dashboard/';
      
      try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setDashboardData(data);
        }
      } catch (error) {
        console.error('Dashboard fetch error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [userRole]);

  return { dashboardData, loading };
};
```

### Task Action Handler
```javascript
export const handleTaskAction = async (taskId, action, reason = '') => {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/tasks/tasks/${taskId}/action/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ action, reason }),
    });
    
    if (response.ok) {
      const result = await response.json();
      return { success: true, data: result };
    } else {
      const error = await response.json();
      return { success: false, error: error.error };
    }
  } catch (error) {
    return { success: false, error: 'Network error' };
  }
};
```

### Stock Entry Component
```javascript
const StockEntryForm = () => {
  const [entries, setEntries] = useState([{
    material_id: '',
    quantity: '',
    reason: '',
    unit_cost: '',
    location: ''
  }]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/inventory/materials/quick_stock_entry/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ entries }),
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Stock updated:', result);
        // Handle success
      }
    } catch (error) {
      console.error('Stock entry error:', error);
    }
  };

  // Form JSX here...
};
```

## 🔄 Real-time Updates

For real-time dashboard updates, implement polling:

```javascript
const useRealTimeUpdates = (interval = 30000) => {
  const [lastCheck, setLastCheck] = useState(new Date().toISOString());
  const [updates, setUpdates] = useState(null);

  useEffect(() => {
    const fetchUpdates = async () => {
      const token = localStorage.getItem('access_token');
      
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/tasks/dashboard/real_time_updates/?last_check=${lastCheck}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        );
        
        if (response.ok) {
          const data = await response.json();
          setUpdates(data);
          setLastCheck(data.timestamp);
        }
      } catch (error) {
        console.error('Real-time updates error:', error);
      }
    };

    const intervalId = setInterval(fetchUpdates, interval);
    return () => clearInterval(intervalId);
  }, [lastCheck, interval]);

  return updates;
};
```

## 🎯 Frontend Views to Implement

### 1. Warehouse Worker Dashboard
- **Path**: `/warehouse-dashboard`
- **Components**: TaskSummary, ActiveTask, TimeTracker, RecentTasks, Notifications
- **API**: `/api/tasks/dashboard/worker_dashboard/`

### 2. Supervisor Dashboard  
- **Path**: `/supervisor-dashboard`
- **Components**: TaskOverview, WorkerStatus, TaskApproval, RecentActivities
- **API**: `/api/tasks/dashboard/supervisor_dashboard/`

### 3. Task Management Views
- **My Tasks**: `/my-tasks` - Worker's task list with start/pause/complete actions
- **Task Assignment**: `/assign-tasks` - Supervisor interface for assigning tasks
- **Task Details**: `/tasks/:id` - Detailed task view with notes and time tracking

### 4. Inventory Management Views
- **Stock Dashboard**: `/inventory` - Material overview with stock levels
- **Stock Entry**: `/stock-entry` - Quick stock entry form
- **Material Details**: `/materials/:id` - Individual material management
- **Low Stock Alerts**: `/alerts` - Critical stock notifications

### 5. Reporting Views
- **Productivity Reports**: `/reports/productivity` - Worker performance metrics
- **Inventory Reports**: `/reports/inventory` - Stock usage and trends
- **Task Analytics**: `/reports/tasks` - Task completion statistics

## 🚨 Error Handling

All endpoints return consistent error formats:

```json
{
  "error": "Error message",
  "details": "Additional details if available",
  "code": "ERROR_CODE"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

## 🔧 Setup Instructions

1. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Set Up Initial Data**:
   ```bash
   python manage.py setup_inventory_data
   python manage.py setup_task_data
   ```

3. **Create Warehouse Workers**:
   ```bash
   python manage.py shell
   from users.models import User
   User.objects.create_user(username='worker1', password='password123', role='warehouse')
   ```

4. **Test API Endpoints**:
   Use the Django admin or API browser at `/api/` to test endpoints.

## 📞 Support

For any questions or issues with the API integration, refer to:
- Django admin panel for data management
- API browser at `/api/` for endpoint testing
- This documentation for reference

---

*This API is designed to fully support all warehouse dashboard frontend views with real-time updates, role-based access, and comprehensive data management.*