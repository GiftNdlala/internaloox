# 🏭 OOX Warehouse Backend Requirements - Frontend Integration

## 🚀 **CRITICAL: FRONTEND IS READY - BACKEND IMPLEMENTATION NEEDED**

The warehouse dashboard frontend is **100% complete and working** with mock data. This document specifies the **exact backend API requirements** to make the frontend fully functional with real data.

### ✅ **Frontend Status**
- **Task Management**: ✅ Complete UI with order-task creation workflow
- **Notifications**: ✅ Working notification bell with dropdown
- **Role-based Access**: ✅ All roles supported (owner, admin, warehouse_manager, warehouse)
- **Mock Data**: ✅ Shows exact expected data structures

### 🎯 **Backend Requirements**
The backend must implement these **exact API endpoints** with the **exact data structures** the frontend expects.

---

## 📋 **1. TASK MANAGEMENT APIs**

### **🔥 CRITICAL: Create Task in Order**
**Endpoint**: `POST /api/orders/{order_id}/create_task/`

**Frontend Expectation**: When admin clicks "Create Task" button on Order OOX000045, this API must:
1. Create a task linked to that specific order
2. Assign it to the selected worker
3. Send notification to the worker
4. Return the created task data

**Request Body** (exactly what frontend sends):
```json
{
  "title": "Cut fabric pieces",
  "description": "Cut fabric for L-shaped couch", 
  "task_type_id": 1,
  "assigned_to_id": 5,
  "priority": "high",
  "estimated_duration": 120,
  "deadline": "2024-12-25T15:00:00Z",
  "instructions": "Follow the pattern carefully",
  "materials_needed": "Suede fabric, cutting tools"
}
```

**Response** (exactly what frontend expects):
```json
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
    "order_number": "OOX000045",
    "deadline": "2024-12-25T15:00:00Z",
    "created_at": "2024-12-16T14:30:00Z"
  }
}
```

### **📋 Get Tasks by Order (Worker View)**
**Endpoint**: `GET /api/tasks/dashboard/tasks_by_order/`

**Frontend Expectation**: Workers see tasks organized by customer orders (NOT flat task lists)

**Response Structure**:
```json
{
  "orders_with_tasks": [
    {
      "order_info": {
        "id": 45,
        "order_number": "OOX000045", 
        "customer_name": "John Doe",
        "delivery_deadline": "2024-12-25",
        "urgency": "high",
        "total_amount": 2500.00
      },
      "tasks": [
        {
          "id": 123,
          "title": "Cut fabric pieces",
          "task_type": "Cutting",
          "status": "assigned",
          "priority": "high",
          "is_running": false,
          "is_overdue": false,
          "time_elapsed_formatted": "0h 0m",
          "total_time_formatted": "0h 0m",
          "can_start": true,
          "can_pause": false,
          "can_complete": false,
          "assigned_to": "Mary Johnson",
          "due_date": "2024-12-25T15:00:00Z",
          "created_at": "2024-12-16T14:30:00Z"
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
```

### **⚡ Enhanced Task Actions**
**Endpoint**: `POST /api/tasks/tasks/{task_id}/perform_action/`

**Frontend Expectation**: Real-time task control with timer tracking

**Request Body**:
```json
{
  "action": "start",  // "start", "pause", "resume", "complete"
  "reason": "Starting work on fabric cutting"
}
```

**Response** (exactly what frontend expects):
```json
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
```

### **📊 Orders Ready for Task Assignment**
**Endpoint**: `GET /api/orders/warehouse_orders/`

**Frontend Expectation**: Admin/Manager sees orders that need task assignment

**Response Structure**:
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
      "total_amount": 5500.00,
      "delivery_deadline": "2024-12-25",
      "is_priority_order": false,
      "can_create_tasks": true
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

---

## 🔔 **2. NOTIFICATION SYSTEM APIs**

### **🔥 CRITICAL: Real-time Updates**
**Endpoint**: `GET /api/tasks/dashboard/real_time_updates/?since=timestamp`

**Frontend Expectation**: Notification bell shows live updates

**Response Structure**:
```json
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
    },
    {
      "id": 46,
      "message": "Task completed: Upholstery work by John Smith",
      "type": "task_completed", 
      "priority": "normal",
      "is_read": false,
      "created_at": "2024-12-16T14:25:00Z",
      "task_id": 124,
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
  "timestamp": "2024-12-16T14:35:00Z"
}
```

### **📬 User Notifications**
**Endpoint**: `GET /api/tasks/notifications/`

**Response Structure**:
```json
[
  {
    "id": 45,
    "message": "New task assigned: Cut fabric pieces",
    "type": "task_assigned",
    "priority": "normal", 
    "is_read": false,
    "created_at": "2024-12-16T14:30:00Z",
    "task": {
      "id": 156,
      "title": "Cut fabric pieces",
      "order_number": "OOX000045"
    }
  }
]
```

### **✅ Mark Notifications Read**
**Endpoint**: `POST /api/tasks/notifications/mark_all_read/`

**Response**:
```json
{
  "message": "5 notifications marked as read",
  "updated_count": 5
}
```

---

## 👥 **3. USER MANAGEMENT & ROLES**

### **🎯 Role-based Access Control**

The frontend supports these **exact roles**:
- `owner` - Full system access
- `admin` - Administrative access
- `warehouse_manager` - Warehouse operations management  
- `warehouse` - Legacy role (warehouse worker)
- `warehouse_worker` - New warehouse worker role

### **👷 Get Warehouse Workers**
**Endpoint**: `GET /api/users/warehouse_workers/`

**Response Structure**:
```json
[
  {
    "id": 5,
    "username": "mary_johnson",
    "first_name": "Mary",
    "last_name": "Johnson",
    "email": "mary@oox.com", 
    "role": "warehouse_worker",
    "employee_id": "WW001",
    "can_manage_tasks": false,
    "is_active": true
  },
  {
    "id": 6,
    "username": "supervisor_tom",
    "first_name": "Tom", 
    "last_name": "Wilson",
    "email": "tom@oox.com",
    "role": "warehouse_manager", 
    "employee_id": "WM001",
    "can_manage_tasks": true,
    "is_active": true
  }
]
```

### **🔐 User Permissions**

**Task Creation Permissions**:
- ✅ `owner`, `admin`, `warehouse_manager` - Can create and assign tasks
- ❌ `warehouse`, `warehouse_worker` - Cannot create tasks, only execute

**Data Access**:
- **Managers/Admin**: See all orders and tasks
- **Workers**: See only their assigned tasks organized by orders

---

## 🎯 **4. TASK TYPES & TEMPLATES**

### **📋 Task Types**
**Endpoint**: `GET /api/tasks/task-types/`

**Response Structure**:
```json
[
  {
    "id": 1,
    "name": "Cutting",
    "description": "Cut materials according to patterns",
    "estimated_duration_minutes": 60,
    "requires_materials": true,
    "is_active": true,
    "color_code": "#ff6b6b"
  },
  {
    "id": 2, 
    "name": "Upholstery",
    "description": "Upholstery and finishing work",
    "estimated_duration_minutes": 180,
    "requires_materials": true,
    "is_active": true,
    "color_code": "#4ecdc4"
  }
]
```

---

## 🚨 **5. CRITICAL IMPLEMENTATION NOTES**

### **🎯 Frontend-Backend Alignment**

1. **Order-Task Relationship**: 
   - Frontend expects tasks to be created **within specific orders**
   - Tasks must be linked to `order_id` in database
   - Worker view shows tasks **grouped by orders**, not flat lists

2. **Real-time Updates**:
   - Frontend polls `/real_time_updates/` every 15 seconds
   - Must return `has_updates: true` when there are new notifications
   - Notification bell badge shows unread count

3. **Role-based Security**:
   - API must check user roles before allowing task creation
   - Workers should only see their own tasks
   - Managers see all tasks and can create/assign

4. **Data Consistency**:
   - All datetime fields must be ISO format: `"2024-12-16T14:30:00Z"`
   - Status fields must match frontend expectations: `"assigned"`, `"started"`, `"completed"`
   - Boolean fields for UI control: `can_start`, `can_pause`, `can_complete`

### **⚡ Performance Requirements**

- **Response Time**: All APIs must respond within 500ms
- **Real-time Updates**: Must handle polling from multiple users
- **Database Queries**: Optimize for order-task joins
- **Caching**: Consider caching for frequently accessed data

---

## 🔧 **6. DEVELOPMENT PRIORITY**

### **Phase 1: CRITICAL (Week 1)**
1. ✅ `POST /api/orders/{id}/create_task/` - Task creation in orders
2. ✅ `GET /api/tasks/dashboard/tasks_by_order/` - Worker task view  
3. ✅ `POST /api/tasks/tasks/{id}/perform_action/` - Task actions
4. ✅ `GET /api/orders/warehouse_orders/` - Orders for task assignment

### **Phase 2: ESSENTIAL (Week 2)**  
1. ✅ `GET /api/tasks/dashboard/real_time_updates/` - Real-time updates
2. ✅ `GET /api/tasks/notifications/` - User notifications
3. ✅ `POST /api/tasks/notifications/mark_all_read/` - Mark as read
4. ✅ `GET /api/users/warehouse_workers/` - Worker list

### **Phase 3: ENHANCEMENT (Week 3)**
1. ✅ `GET /api/tasks/task-types/` - Task types
2. ✅ Bulk assignment endpoints
3. ✅ Advanced filtering and search
4. ✅ Analytics and reporting

---

## 🎉 **FRONTEND TESTING CHECKLIST**

Once backend APIs are implemented, test these **exact scenarios**:

### **Admin/Manager Workflow**
1. ✅ Login as admin → See warehouse dashboard
2. ✅ Click "Task Management" tab → See orders ready for tasks  
3. ✅ Click "Create Task" on Order OOX000045 → Modal opens
4. ✅ Fill form: Title, Worker, Priority → Submit successfully
5. ✅ See task created in tasks table → Shows in correct order
6. ✅ Notification bell shows new activity → Badge updates

### **Worker Workflow**  
1. ✅ Login as warehouse worker → See "My Tasks"
2. ✅ Tasks organized by customer orders → Not flat lists
3. ✅ Click task → See order context and details
4. ✅ Start task → Timer begins, status updates
5. ✅ Complete task → Notification sent to manager

### **Real-time Features**
1. ✅ Notification bell shows unread count
2. ✅ Click bell → See notification dropdown  
3. ✅ "Mark all read" → Badge disappears
4. ✅ Live updates without page refresh

---

## 📞 **SUPPORT & INTEGRATION**

### **Frontend Team Ready** ✅
- Complete UI implementation with mock data
- All components tested and working
- Role-based access implemented  
- Professional styling complete

### **Backend Team Needed** 🔄
- Implement exact API endpoints listed above
- Match exact data structures specified
- Ensure role-based permissions
- Test with frontend integration

### **Integration Process**
1. Backend implements Phase 1 APIs
2. Frontend switches from mock to real data
3. Test critical workflows (task creation, worker view)
4. Implement Phase 2 (notifications, real-time)
5. Final testing and production deployment

---

## 🚀 **READY FOR PRODUCTION**

Once these backend APIs are implemented with the **exact specifications** above, the warehouse dashboard will be:

- ✅ **Fully Functional**: Complete order-task workflow
- ✅ **Real-time**: Live notifications and updates
- ✅ **Role-based**: Proper access control for all user types  
- ✅ **Professional**: Production-ready UI/UX
- ✅ **Mobile-optimized**: Works on all devices

**The frontend is ready - we just need the backend APIs! 🎯**

---

*Backend Requirements Document*  
*Created: December 16, 2024*  
*Status: 🔄 AWAITING BACKEND IMPLEMENTATION*  
*Frontend Status: ✅ 100% COMPLETE AND READY*