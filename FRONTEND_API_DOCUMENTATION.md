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

## 📋 Order-Task Management Workflow

### 1. Get Warehouse Orders (For Task Assignment)
**GET** `/api/orders/warehouse_orders/`

Returns orders ready for warehouse processing, organized by urgency.

**Response:**
```json
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
      "total_amount": 5500.00
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
```

### 2. Get Order Details for Task Assignment
**GET** `/api/orders/{order_id}/order_details_for_tasks/`

Returns detailed order information including items and existing tasks.

**Response:**
```json
{
  "order": {
    "id": 45,
    "order_number": "OOX000045",
    "customer_name": "John Doe",
    "delivery_deadline": "2024-12-25",
    "total_amount": 5500.00
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
          "material_name": "Suede Fabric",
          "total_needed": 15.5,
          "unit": "Meters"
        }
      ]
    }
  ],
  "existing_tasks": [...],
  "task_summary": {
    "total_tasks": 2,
    "completed": 0,
    "in_progress": 1,
    "pending": 1
  }
}
```

### 3. Assign Multiple Tasks to Order
**POST** `/api/orders/{order_id}/assign_tasks_to_order/`

Assigns multiple tasks to an order with specific workers.

**Request Body:**
```json
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
          "quantity_needed": 15.5
        }
      ]
    },
    {
      "task_type_id": 5,
      "assigned_to_id": 7,
      "title": "Upholstery - Order OOX000045",
      "priority": "high",
      "due_date": "2024-12-23T16:00:00Z"
    }
  ]
}
```

### 4. Get Orders with Tasks (Supervisor View)
**GET** `/api/tasks/dashboard/orders_with_tasks/`

Returns orders organized by task completion status.

**Response:**
```json
{
  "orders_by_status": {
    "no_tasks": [...],
    "in_progress": [...],
    "completed": [...],
    "mixed_status": [...]
  },
  "summary": {
    "no_tasks": 3,
    "in_progress": 5,
    "completed": 2,
    "total_orders": 10
  }
}
```

### 5. Get Tasks by Order (Worker View)
**GET** `/api/tasks/dashboard/tasks_by_order/`

Returns tasks organized by order for warehouse workers.

**Response:**
```json
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
          "is_running": false,
          "can_start": true,
          "can_pause": false,
          "can_complete": false
        }
      ]
    }
  ]
}
```

## 📋 Task Management Endpoints

### 1. Get My Tasks (Worker View)
**GET** `/api/tasks/tasks/my_tasks/`

Returns tasks assigned to the current user.

### 2. Task Actions (Start, Pause, Complete)
**POST** `/api/tasks/tasks/{task_id}/perform_action/`

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

### Order-Task Assignment Component
```javascript
const OrderTaskAssignment = ({ orderId }) => {
  const [orderDetails, setOrderDetails] = useState(null);
  const [availableWorkers, setAvailableWorkers] = useState([]);
  const [taskTypes, setTaskTypes] = useState([]);
  const [tasksToAssign, setTasksToAssign] = useState([]);

  useEffect(() => {
    fetchOrderDetails();
    fetchAssignmentData();
  }, [orderId]);

  const fetchOrderDetails = async () => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/api/orders/${orderId}/order_details_for_tasks/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.ok) {
      const data = await response.json();
      setOrderDetails(data);
    }
  };

  const assignTasksToOrder = async () => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/api/orders/${orderId}/assign_tasks_to_order/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ tasks: tasksToAssign }),
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('Tasks assigned:', result);
      // Refresh order details
      fetchOrderDetails();
    }
  };

  const addTask = () => {
    setTasksToAssign([...tasksToAssign, {
      task_type_id: '',
      assigned_to_id: '',
      title: '',
      priority: 'normal',
      due_date: ''
    }]);
  };

  return (
    <div className="order-task-assignment">
      {orderDetails && (
        <>
          <div className="order-header">
            <h2>{orderDetails.order.order_number}</h2>
            <p>Customer: {orderDetails.order.customer_name}</p>
            <p>Deadline: {orderDetails.order.delivery_deadline}</p>
          </div>
          
          <div className="existing-tasks">
            <h3>Existing Tasks ({orderDetails.task_summary.total_tasks})</h3>
            {orderDetails.existing_tasks.map(task => (
              <div key={task.id} className="task-item">
                <span>{task.title}</span>
                <span>Assigned to: {task.assigned_to}</span>
                <span className={`status ${task.status}`}>{task.status}</span>
              </div>
            ))}
          </div>
          
          <div className="new-tasks">
            <h3>Assign New Tasks</h3>
            {tasksToAssign.map((task, index) => (
              <div key={index} className="task-form">
                <select 
                  value={task.task_type_id}
                  onChange={(e) => {
                    const updated = [...tasksToAssign];
                    updated[index].task_type_id = e.target.value;
                    setTasksToAssign(updated);
                  }}
                >
                  <option value="">Select Task Type</option>
                  {taskTypes.map(type => (
                    <option key={type.id} value={type.id}>{type.name}</option>
                  ))}
                </select>
                
                <select 
                  value={task.assigned_to_id}
                  onChange={(e) => {
                    const updated = [...tasksToAssign];
                    updated[index].assigned_to_id = e.target.value;
                    setTasksToAssign(updated);
                  }}
                >
                  <option value="">Select Worker</option>
                  {availableWorkers.map(worker => (
                    <option key={worker.id} value={worker.id}>
                      {worker.name} ({worker.active_tasks_count} active)
                    </option>
                  ))}
                </select>
                
                <input 
                  type="text"
                  placeholder="Task title"
                  value={task.title}
                  onChange={(e) => {
                    const updated = [...tasksToAssign];
                    updated[index].title = e.target.value;
                    setTasksToAssign(updated);
                  }}
                />
              </div>
            ))}
            
            <button onClick={addTask}>Add Task</button>
            <button onClick={assignTasksToOrder}>Assign All Tasks</button>
          </div>
        </>
      )}
    </div>
  );
};
```

### Worker Order-Task View Component
```javascript
const WorkerOrderTasks = () => {
  const [ordersWithTasks, setOrdersWithTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTasksByOrder();
  }, []);

  const fetchTasksByOrder = async () => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/api/tasks/dashboard/tasks_by_order/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      const data = await response.json();
      setOrdersWithTasks(data.orders_with_tasks);
    }
    setLoading(false);
  };

  const handleTaskAction = async (taskId, action) => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/api/tasks/tasks/${taskId}/perform_action/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ action }),
    });
    
    if (response.ok) {
      // Refresh the tasks
      fetchTasksByOrder();
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="worker-order-tasks">
      <h2>My Tasks by Order</h2>
      
      {ordersWithTasks.map(orderGroup => (
        <div key={orderGroup.order_info.id} className="order-group">
          <div className={`order-header ${orderGroup.order_info.urgency}`}>
            <h3>{orderGroup.order_info.order_number}</h3>
            <p>Customer: {orderGroup.order_info.customer_name}</p>
            <p>Deadline: {orderGroup.order_info.delivery_deadline}</p>
            <span className={`urgency-badge ${orderGroup.order_info.urgency}`}>
              {orderGroup.order_info.urgency.toUpperCase()}
            </span>
          </div>
          
          <div className="tasks-list">
            {orderGroup.tasks.map(task => (
              <div key={task.id} className={`task-card ${task.status}`}>
                <div className="task-info">
                  <h4>{task.title}</h4>
                  <p>Type: {task.task_type}</p>
                  <p>Status: {task.status}</p>
                  {task.is_running && (
                    <p className="time-elapsed">
                      Time: {task.time_elapsed_formatted}
                    </p>
                  )}
                </div>
                
                <div className="task-actions">
                  {task.can_start && (
                    <button 
                      onClick={() => handleTaskAction(task.id, 'start')}
                      className="btn-start"
                    >
                      Start
                    </button>
                  )}
                  {task.can_pause && (
                    <button 
                      onClick={() => handleTaskAction(task.id, 'pause')}
                      className="btn-pause"
                    >
                      Pause
                    </button>
                  )}
                  {task.can_complete && (
                    <button 
                      onClick={() => handleTaskAction(task.id, 'complete')}
                      className="btn-complete"
                    >
                      Complete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
```

### Task Action Handler
```javascript
export const handleTaskAction = async (taskId, action, reason = '') => {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/tasks/tasks/${taskId}/perform_action/`, {
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

### 3. Order-Task Management Views (NEW)
- **Orders for Today**: `/orders-today` - Orders ready for warehouse processing
- **Order Task Assignment**: `/orders/:id/assign-tasks` - Assign multiple tasks to an order
- **Worker Order View**: `/my-orders` - Worker's tasks organized by order
- **Order Progress**: `/orders/:id/progress` - Track task completion for specific order

### 4. Task Management Views
- **My Tasks**: `/my-tasks` - Worker's task list with start/pause/complete actions  
- **My Tasks by Order**: `/my-tasks-by-order` - Tasks grouped by order (RECOMMENDED)
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