# 🏭 OOX Warehouse Backend Requirements - Frontend Integration

## 🚨 **URGENT: FRONTEND TEAM HAS ALREADY IMPLEMENTED THESE ENDPOINTS**

Hey Backend Team! 👋

The frontend team has **already implemented** all the warehouse dashboard features and is **waiting for you** to make these API endpoints work with real data. The frontend is **100% complete** and deployed, but currently shows "Loading..." or "No data available" because these endpoints aren't returning the expected data yet.

**Please ensure your backend configurations match exactly what the frontend is already calling.** The frontend is already making requests to these endpoints - we just need you to make them return the right data!

## 🔧 **CURRENT BACKEND STATUS**

### ✅ **Already Implemented in This Django Backend**
We've already created the models and basic endpoints, but they need to be **configured to return the exact data formats** the frontend expects:

- ✅ **Models**: User (with new roles), Task, Notification, TaskType, etc.
- ✅ **Basic Endpoints**: Task CRUD, User management, Order management
- ✅ **Database**: Migrations applied, schema ready
- ✅ **Authentication**: JWT token system working

### 🔄 **What Needs to be Done**
The endpoints exist but need to be **updated to match frontend expectations**:

1. **Data Format Alignment**: Ensure JSON responses match frontend expectations
2. **Role-based Filtering**: Apply correct permissions based on user roles  
3. **Real-time Updates**: Configure polling endpoints properly
4. **Worker Assignment**: Populate dropdowns with correct user data 

## 🎯 **FRONTEND STATUS: ✅ DEPLOYED AND WAITING**

### ✅ **Already Implemented on Frontend**
- **Task Management Dashboard**: ✅ Complete UI with order-task creation workflow  
- **Notification System**: ✅ Real-time notification bell with dropdown
- **Role-based Navigation**: ✅ Admin, Owner, Warehouse Manager, Worker views
- **Auto-refresh**: ✅ Extended intervals (30s instead of every second)
- **Navigation Bars**: ✅ All dashboard types have proper navigation
- **Mobile Responsive**: ✅ Works on all devices

### 🔄 **What's Waiting for Backend**
The frontend is **already calling these endpoints** but getting empty responses or errors. Please implement these exact endpoints with the exact data structures specified below.

### ⚡ **Auto-refresh Configuration (ALREADY IMPLEMENTED)**
- **Dashboard Overview**: Refreshes every **30 seconds** (was 1 second - now optimized)
- **Task Management**: Refreshes every **20 seconds** 
- **Worker Task View**: Refreshes every **15 seconds**
- **Notifications**: Polls every **10 seconds** for real-time updates
- **Inventory**: Refreshes every **60 seconds**

### 🧭 **Navigation Implementation (ALREADY DONE)**
- **Admin Dashboard**: Has Task Management tab with order-task workflow
- **Owner Dashboard**: Has Task Management tab with full access
- **Warehouse Manager**: Has Task Management tab with worker assignment
- **Warehouse Worker**: Has "My Tasks" view organized by orders
- **All Views**: Have proper navigation bars and role-based menus

### ✅ **Frontend Status**
- **Task Management**: ✅ Complete UI with order-task creation workflow
- **Notifications**: ✅ Working notification bell with dropdown
- **Role-based Access**: ✅ All roles supported (owner, admin, warehouse_manager, warehouse)
- **Mock Data**: ✅ Shows exact expected data structures

### 🎯 **Backend Requirements**
The backend must implement these **exact API endpoints** with the **exact data structures** the frontend expects.

---

## 📋 **1. TASK MANAGEMENT APIs - ADMIN/OWNER DASHBOARD**

### **🔥 CRITICAL: Admin/Owner Task Management Tab**

**Frontend Implementation**: Admin and Owner dashboards **already have** a "Task Management" tab that shows:
1. Orders ready for task assignment (with "Create Task" buttons)
2. Task creation modal with worker assignment dropdown
3. Real-time task table with filtering and sorting
4. Notification system integration

**Backend Requirement**: Make these endpoints return real data instead of empty responses.

---

## 📋 **1. TASK MANAGEMENT APIs**

### **🔥 CRITICAL: Create Task in Order**
**Endpoint**: `POST /api/orders/{order_id}/create_task/`

**Frontend Expectation**: When admin/owner clicks "Create Task" button on Order OOX000045, this API must:
1. Create a task linked to that specific order
2. Assign it to the selected worker (from dropdown populated by `/api/users/warehouse_workers/`)
3. Send notification to the worker
4. Return the created task data

**UI Flow Already Implemented**:
1. Admin/Owner goes to Task Management tab
2. Sees orders ready for task assignment
3. Clicks "Create Task" on next order to be completed
4. Modal opens with:
   - Task title and description fields
   - Task type dropdown (populated by `/api/tasks/task-types/`)
   - **Worker assignment dropdown** (populated by `/api/users/warehouse_workers/`)
   - Priority selection
   - Deadline picker
   - Instructions text area

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

## 🔧 **6. BACKEND DEVELOPMENT PRIORITY**

### **⚡ URGENT: CRITICAL APIs (Deploy ASAP)**
**Frontend is already calling these - need immediate implementation:**

1. 🚨 `POST /api/orders/{id}/create_task/` - **CRITICAL**: Task creation in orders
2. 🚨 `GET /api/tasks/dashboard/tasks_by_order/` - **CRITICAL**: Worker task view  
3. 🚨 `GET /api/orders/warehouse_orders/` - **CRITICAL**: Orders for task assignment
4. 🚨 `GET /api/users/warehouse_workers/` - **CRITICAL**: Worker dropdown list

### **🔥 HIGH PRIORITY: Essential Features (Week 1)**  
5. ⚡ `POST /api/tasks/tasks/{id}/perform_action/` - Task actions (start/pause/complete)
6. ⚡ `GET /api/tasks/dashboard/real_time_updates/` - Real-time updates
7. ⚡ `GET /api/tasks/notifications/` - User notifications
8. ⚡ `GET /api/tasks/task-types/` - Task type dropdown

### **📈 MEDIUM PRIORITY: Enhancement (Week 2)**
9. 📊 `POST /api/tasks/notifications/mark_all_read/` - Mark notifications as read
10. 📊 Bulk assignment endpoints
11. 📊 Advanced filtering and search
12. 📊 Analytics and reporting

**🎯 Focus Order**: Implement in exact order above - frontend is waiting for #1-4 immediately!

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

## 📞 **BACKEND TEAM ACTION ITEMS**

### **✅ Frontend Team Status: COMPLETE & DEPLOYED**
- ✅ Complete UI implementation (no mock data - waiting for real APIs)
- ✅ All components tested and working
- ✅ Role-based access implemented for all user types
- ✅ Professional styling and mobile responsiveness complete
- ✅ Auto-refresh optimized (extended intervals)
- ✅ Navigation bars added to all dashboard types
- ✅ Task management integrated into Admin/Owner dashboards
- ✅ Notification system with real-time bell

### **🔄 Backend Team TODO: IMPLEMENT THESE EXACT ENDPOINTS**
**The frontend is deployed and making requests to these URLs right now:**

1. **URGENT**: Make `POST /api/orders/{id}/create_task/` work
2. **URGENT**: Make `GET /api/orders/warehouse_orders/` return orders
3. **URGENT**: Make `GET /api/users/warehouse_workers/` return worker list  
4. **URGENT**: Make `GET /api/tasks/dashboard/tasks_by_order/` return task data

**Frontend is literally waiting for you - users see "Loading..." or empty states!**

### **🚀 Deployment Process**
1. ✅ **Frontend**: Already deployed and live
2. 🔄 **Backend**: Implement critical APIs (#1-4 above)
3. 🔄 **Backend**: Deploy your changes
4. ✅ **Integration**: Will work immediately (frontend already configured)
5. ✅ **Testing**: Frontend team will verify functionality

---

## 🎯 **SUMMARY FOR BACKEND TEAM**

### **What You Need to Do RIGHT NOW:**

1. **Check your current API endpoints** - frontend is calling them but getting errors/empty data
2. **Implement the 4 critical endpoints** listed in priority section above
3. **Match the exact response formats** - frontend expects specific JSON structures
4. **Deploy your changes** - frontend will immediately start working

### **What Happens When You're Done:**

The warehouse dashboard will **immediately** become:
- ✅ **Fully Functional**: Complete order-task workflow working
- ✅ **Real-time**: Live notifications and updates working
- ✅ **Role-based**: All user types (Admin, Owner, Manager, Worker) working
- ✅ **Professional**: Production-ready UI/UX already deployed
- ✅ **Mobile-optimized**: Already responsive on all devices

### **🔥 CRITICAL SUCCESS FACTORS:**

1. **Exact JSON Structures**: Frontend expects specific field names and formats
2. **Role-based Permissions**: API must check user roles before returning data
3. **Order-Task Relationships**: Tasks must be linked to specific orders
4. **Real-time Compatibility**: APIs must support frequent polling

**🚨 Frontend team is waiting - implement these 4 critical APIs and we're live! 🚀**

---

## Add Product API Alignment (Confirmation)

- Endpoint: `POST /api/products/`
- Auth: JWT Bearer; role required in `{'owner','admin','warehouse_manager','warehouse'}` for create. Reads remain open.
- Request body accepted (labels or nulls):
  - `name` (string, required)
  - `sku` (string, optional) → stored as `model_code`
  - `description` (string, optional)
  - `price` (number, required) → stored as `unit_price`
  - `currency` (string, optional, default `ZAR`) → echoed back in response
  - `color` (string label, optional)
  - `fabric` (string label, optional)
  - `attributes` (object map, optional) → persisted in `Product.attributes` JSONField
- Response: `201 Created` with created product, including `name`, `sku`, `price`, `currency`, `color`, `fabric`, `attributes`, `created_at`.
- Errors: `400` for validation with `{error: string}` or field errors. Permission errors `403` when role/auth missing.
- Reference data endpoints available:
  - `GET /api/colors/`
  - `GET /api/fabrics/`

This aligns with the frontend Add Product contract and is production-ready.

*Backend Requirements Document*  
*Updated: December 16, 2024*  
*Status: 🚨 URGENT - FRONTEND DEPLOYED, WAITING FOR BACKEND*  
*Frontend Status: ✅ 100% COMPLETE AND DEPLOYED*  
*Backend Status: 🔄 CRITICAL APIS NEEDED IMMEDIATELY*