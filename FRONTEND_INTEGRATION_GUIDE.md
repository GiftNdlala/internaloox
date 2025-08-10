# 🎨 Frontend Integration Guide - Warehouse Worker Implementation

## 📅 Updated: December 16, 2024
## 🎯 Status: Backend COMPLETE - Frontend Integration Required
## 👥 For: Frontend Development Team

---

## 🚨 **URGENT: BACKEND IS READY - AWAITING FRONTEND UPDATES**

The backend warehouse worker functionality is **100% complete** and production-ready. The frontend team needs to implement the following updates to support the new worker role system.

---

## 🔧 **REQUIRED FRONTEND CHANGES**

### 1. **Update Workers Page API Calls** ⚡ CRITICAL

#### **Current Implementation Status**: ✅ UI Complete, 🔄 API Integration Needed

**What's Already Working**:
- ✅ Workers page at `/#/warehouse/workers`
- ✅ List view with search and filtering UI
- ✅ Create/Edit/Delete modals
- ✅ Task history modal interface

**What Needs to be Updated**:

#### **A. Role-Based Filtering**
Replace current API calls with new role-based endpoints:

```javascript
// OLD - Remove this
GET /api/users/users/

// NEW - Use role-based filtering
GET /api/users/users/?role=warehouse_worker
GET /api/users/users/?role=warehouse_manager
GET /api/users/users/?role=delivery
```

#### **B. Worker Creation with Permissions**
Update the create worker modal to respect role-based permissions:

```javascript
// Frontend should check user role and limit options
const userRole = getCurrentUser().role;
const allowedRoles = {
  'owner': ['owner', 'admin', 'warehouse_manager', 'warehouse_worker', 'delivery'],
  'admin': ['warehouse_manager', 'warehouse_worker', 'delivery'],
  'warehouse_manager': ['warehouse_worker']
};

// Only show role options that current user can create
const availableRoles = allowedRoles[userRole] || [];
```

#### **C. Task History Modal**
Update the task history modal to use the new worker filtering:

```javascript
// NEW - Use assigned_worker parameter
async function loadWorkerTaskHistory(workerId) {
  const response = await fetch(`/api/tasks/tasks/?assigned_worker=${workerId}`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  return response.json();
}
```

### 2. **Implement Worker Dashboard** 🆕 NEW FEATURE

#### **Create New Route**: `/#/warehouse/worker`

This is a **completely new interface** for warehouse workers. The backend is ready with comprehensive APIs.

#### **Main Dashboard Component**:

```javascript
// WorkerDashboard.jsx
import React, { useState, useEffect } from 'react';

function WorkerDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(loadDashboardData, 15000);
    return () => clearInterval(interval);
  }, []);

  async function loadDashboardData() {
    try {
      const response = await fetch('/api/tasks/dashboard/worker_dashboard/', {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      setDashboardData(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    }
  }

  // Quick action functions
  async function startNextTask() {
    const response = await fetch('/api/tasks/dashboard/quick_start_next_task/', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      loadDashboardData(); // Refresh dashboard
    }
  }

  async function pauseActiveTask() {
    const response = await fetch('/api/tasks/dashboard/quick_pause_active_task/', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reason: 'Manual pause' })
    });
    
    if (response.ok) {
      loadDashboardData(); // Refresh dashboard
    }
  }

  async function completeActiveTask() {
    const notes = prompt('Completion notes (optional):');
    const response = await fetch('/api/tasks/dashboard/quick_complete_active_task/', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ completion_notes: notes || '' })
    });
    
    if (response.ok) {
      loadDashboardData(); // Refresh dashboard
    }
  }

  if (loading) return <div>Loading dashboard...</div>;

  return (
    <div className="worker-dashboard">
      {/* Worker Info Card */}
      <div className="worker-info-card">
        <h2>Welcome, {dashboardData.worker_info.name}</h2>
        <p>Role: {dashboardData.worker_info.role}</p>
        <p>Employee ID: {dashboardData.worker_info.employee_id}</p>
      </div>

      {/* Task Summary */}
      <div className="task-summary-grid">
        <div className="stat-card">
          <h3>Total Tasks</h3>
          <span className="stat-number">{dashboardData.task_summary.total_tasks}</span>
        </div>
        <div className="stat-card">
          <h3>In Progress</h3>
          <span className="stat-number">{dashboardData.task_summary.in_progress}</span>
        </div>
        <div className="stat-card">
          <h3>Completed Today</h3>
          <span className="stat-number">{dashboardData.task_summary.completed_today}</span>
        </div>
        <div className="stat-card urgent">
          <h3>Overdue</h3>
          <span className="stat-number">{dashboardData.task_summary.overdue}</span>
        </div>
      </div>

      {/* Active Task Card */}
      {dashboardData.active_task && (
        <div className="active-task-card">
          <h3>🟡 Current Task</h3>
          <h4>{dashboardData.active_task.title}</h4>
          <p>Order: {dashboardData.active_task.order_number}</p>
          <p>Priority: {dashboardData.active_task.priority}</p>
          <p>Time Running: {dashboardData.time_tracking.time_elapsed_today_formatted}</p>
          
          <div className="task-actions">
            {dashboardData.quick_actions.can_pause && (
              <button onClick={pauseActiveTask} className="btn-pause">
                ⏸️ Pause Task
              </button>
            )}
            {dashboardData.quick_actions.can_complete && (
              <button onClick={completeActiveTask} className="btn-complete">
                ✅ Complete Task
              </button>
            )}
          </div>
        </div>
      )}

      {/* Next Task Card */}
      {dashboardData.next_task && (
        <div className="next-task-card">
          <h3>📋 Next Task</h3>
          <h4>{dashboardData.next_task.title}</h4>
          <p>Order: {dashboardData.next_task.order_number}</p>
          <p>Priority: {dashboardData.next_task.priority}</p>
          
          {dashboardData.quick_actions.can_start_task && (
            <button onClick={startNextTask} className="btn-start">
              ▶️ Start Task
            </button>
          )}
        </div>
      )}

      {/* Recent Tasks */}
      <div className="recent-tasks">
        <h3>Recent Tasks</h3>
        <div className="task-list">
          {dashboardData.recent_tasks.map(task => (
            <div key={task.id} className="task-item">
              <span className="task-title">{task.title}</span>
              <span className="task-status">{task.status}</span>
              <span className="task-order">{task.order_number}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default WorkerDashboard;
```

### 3. **Update Role-Based Navigation** ⚡ CRITICAL

#### **A. Login Component Updates**
Add role selection dropdown to login form:

```javascript
// Login.jsx
function Login() {
  const [selectedRole, setSelectedRole] = useState('');
  
  async function handleLogin(credentials) {
    const response = await fetch('/api/users/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: credentials.username,
        password: credentials.password,
        role: selectedRole // Send selected role
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Store tokens and user data
      localStorage.setItem('token', data.access);
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('selected_role', data.selected_role);
      
      // Route based on selected role
      routeBasedOnRole(data.selected_role || data.user.role);
    }
  }

  function routeBasedOnRole(role) {
    switch(role) {
      case 'warehouse_worker':
      case 'warehouse':
        navigate('/#/warehouse/worker');
        break;
      case 'warehouse_manager':
        navigate('/#/warehouse/manager');
        break;
      case 'admin':
        navigate('/#/admin');
        break;
      case 'owner':
        navigate('/#/owner');
        break;
      case 'delivery':
        navigate('/#/delivery');
        break;
      default:
        navigate('/#/dashboard');
    }
  }

  return (
    <form onSubmit={handleLogin}>
      {/* Username and password fields */}
      
      {/* Role selection for testing */}
      <select 
        value={selectedRole} 
        onChange={(e) => setSelectedRole(e.target.value)}
      >
        <option value="">Use Default Role</option>
        <option value="warehouse_worker">View as Warehouse Worker</option>
        <option value="warehouse_manager">View as Warehouse Manager</option>
        <option value="admin">View as Admin</option>
        <option value="owner">View as Owner</option>
        <option value="delivery">View as Delivery</option>
      </select>
      
      <button type="submit">Login</button>
    </form>
  );
}
```

#### **B. Navigation Component Updates**
Update navigation to show different menus based on role:

```javascript
// Navigation.jsx
function Navigation() {
  const user = getCurrentUser();
  const selectedRole = localStorage.getItem('selected_role') || user.role;

  const navigationItems = {
    'warehouse_worker': [
      { label: 'My Dashboard', path: '/#/warehouse/worker' },
      { label: 'My Tasks', path: '/#/warehouse/worker/tasks' },
      { label: 'Notifications', path: '/#/warehouse/worker/notifications' }
    ],
    'warehouse_manager': [
      { label: 'Overview', path: '/#/warehouse/overview' },
      { label: 'Workers', path: '/#/warehouse/workers' },
      { label: 'Tasks', path: '/#/warehouse/tasks' },
      { label: 'Inventory', path: '/#/warehouse/inventory' }
    ],
    'admin': [
      { label: 'Dashboard', path: '/#/admin' },
      { label: 'Users', path: '/#/admin/users' },
      { label: 'Tasks', path: '/#/admin/tasks' },
      { label: 'Reports', path: '/#/admin/reports' }
    ]
  };

  const items = navigationItems[selectedRole] || [];

  return (
    <nav className="main-navigation">
      {items.map(item => (
        <a key={item.path} href={item.path} className="nav-item">
          {item.label}
        </a>
      ))}
    </nav>
  );
}
```

### 4. **Real-time Updates Implementation** 🔄 PERFORMANCE

#### **A. Dashboard Auto-refresh**
Implement smart refresh intervals:

```javascript
// useRealTimeUpdates.js
import { useState, useEffect } from 'react';

function useRealTimeUpdates(intervalMs = 15000) {
  const [lastUpdate, setLastUpdate] = useState(new Date().toISOString());
  const [updates, setUpdates] = useState({});

  useEffect(() => {
    async function checkForUpdates() {
      try {
        const response = await fetch(
          `/api/tasks/dashboard/real_time_updates/?since=${lastUpdate}`,
          {
            headers: { 'Authorization': `Bearer ${getToken()}` }
          }
        );
        
        const data = await response.json();
        
        if (data.has_updates) {
          setUpdates(data);
          
          // Update notifications
          if (data.notifications.length > 0) {
            showNotifications(data.notifications);
          }
          
          // Trigger dashboard refresh
          window.dispatchEvent(new CustomEvent('dashboardUpdate', { detail: data }));
        }
        
        setLastUpdate(data.timestamp);
      } catch (error) {
        console.error('Failed to check for updates:', error);
      }
    }

    const interval = setInterval(checkForUpdates, intervalMs);
    checkForUpdates(); // Initial check

    return () => clearInterval(interval);
  }, [intervalMs, lastUpdate]);

  return updates;
}

export default useRealTimeUpdates;
```

#### **B. Notification System**
Update notification bell to show real-time updates:

```javascript
// NotificationBell.jsx
function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadNotifications();
    
    // Listen for real-time updates
    window.addEventListener('dashboardUpdate', handleRealTimeUpdate);
    
    return () => {
      window.removeEventListener('dashboardUpdate', handleRealTimeUpdate);
    };
  }, []);

  function handleRealTimeUpdate(event) {
    const updates = event.detail;
    if (updates.notifications && updates.notifications.length > 0) {
      setNotifications(prev => [...updates.notifications, ...prev]);
      setUnreadCount(prev => prev + updates.notifications.length);
    }
  }

  async function loadNotifications() {
    const response = await fetch('/api/tasks/notifications/', {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await response.json();
    setNotifications(data);
    setUnreadCount(data.filter(n => !n.is_read).length);
  }

  async function markAllRead() {
    await fetch('/api/tasks/notifications/mark_all_read/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    setUnreadCount(0);
    loadNotifications();
  }

  return (
    <div className="notification-bell">
      <button className="bell-icon">
        🔔
        {unreadCount > 0 && (
          <span className="badge">{unreadCount}</span>
        )}
      </button>
      
      <div className="notification-dropdown">
        <div className="notification-header">
          <span>Notifications</span>
          <button onClick={markAllRead}>Mark All Read</button>
        </div>
        
        <div className="notification-list">
          {notifications.map(notification => (
            <div key={notification.id} className={`notification-item ${!notification.is_read ? 'unread' : ''}`}>
              <p>{notification.message}</p>
              <small>{new Date(notification.created_at).toLocaleString()}</small>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## 🎨 **UI/UX REQUIREMENTS**

### **Worker Dashboard Design** 🎯

#### **Key UI Components**:

1. **Worker Info Card**
   - Worker name and employee ID
   - Current shift times
   - Role badge

2. **Task Summary Grid**
   - Total tasks assigned
   - Tasks in progress
   - Completed today
   - Overdue tasks (highlighted in red)

3. **Active Task Card**
   - Current running task details
   - Real-time timer
   - Pause/Complete buttons
   - Progress indicator

4. **Next Task Queue**
   - Next assigned task preview
   - Priority indicator
   - Start button

5. **Quick Action Buttons**
   - Large, easily clickable buttons
   - Color-coded actions (green for start, yellow for pause, red for stop)
   - Disabled states when actions not available

6. **Time Tracking Display**
   - Today's total work time
   - Current task elapsed time
   - Formatted time display (e.g., "6h 45m")

#### **Design Specifications**:

```css
/* Worker Dashboard Styles */
.worker-dashboard {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.worker-info-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.task-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  grid-column: 1 / -1;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-card.urgent {
  border-left: 4px solid #dc3545;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #007bff;
}

.active-task-card {
  background: #fff3cd;
  border: 2px solid #ffc107;
  padding: 20px;
  border-radius: 8px;
  grid-column: 1 / -1;
}

.next-task-card {
  background: #d1ecf1;
  border: 2px solid #bee5eb;
  padding: 20px;
  border-radius: 8px;
}

.task-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.btn-start {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1rem;
}

.btn-pause {
  background: #ffc107;
  color: #212529;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1rem;
}

.btn-complete {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1rem;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .worker-dashboard {
    grid-template-columns: 1fr;
    padding: 10px;
  }
  
  .task-summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

---

## 🧪 **TESTING CHECKLIST**

### **1. User Role Testing**
- [ ] Owner can create all role types
- [ ] Admin can create warehouse_manager, warehouse_worker, delivery
- [ ] Warehouse Manager can only create warehouse_worker
- [ ] Workers cannot create any users
- [ ] Role filtering works correctly in Workers page

### **2. Worker Dashboard Testing**
- [ ] Dashboard loads for warehouse workers
- [ ] Quick actions work (start, pause, complete)
- [ ] Real-time updates refresh dashboard
- [ ] Time tracking displays correctly
- [ ] Mobile responsive design works

### **3. Navigation Testing**
- [ ] Role selection in login works
- [ ] Navigation shows appropriate items for each role
- [ ] Worker dashboard accessible at /#/warehouse/worker
- [ ] Proper redirects based on selected role

### **4. API Integration Testing**
- [ ] All new API endpoints return expected data
- [ ] Error handling works for failed requests
- [ ] Authentication headers sent correctly
- [ ] Real-time polling doesn't cause performance issues

---

## 🚀 **DEPLOYMENT STEPS**

### **Phase 1: Backend Verification** ✅ COMPLETE
- ✅ All API endpoints implemented
- ✅ Role-based permissions working
- ✅ Database migrations applied

### **Phase 2: Frontend Updates** 📋 PENDING
1. **Update Workers Page**
   - Replace API calls with role-based filtering
   - Update create/edit modals with permission checks
   - Test task history modal with new API

2. **Implement Worker Dashboard**
   - Create new route and components
   - Implement quick action buttons
   - Add real-time refresh functionality

3. **Update Navigation**
   - Add role selection to login
   - Update navigation based on role
   - Test routing for all roles

### **Phase 3: Testing & Optimization** 📋 PENDING
1. **Comprehensive Testing**
   - Test all role combinations
   - Verify mobile responsiveness
   - Check performance with real-time updates

2. **Performance Optimization**
   - Optimize refresh intervals
   - Implement efficient state management
   - Add loading states and error handling

---

## 📞 **SUPPORT & QUESTIONS**

### **Backend APIs Ready**: ✅
All backend endpoints are implemented and tested. The API responses match exactly what's documented in this guide.

### **Frontend Team Next Steps**:
1. **Immediate**: Update Workers page API calls
2. **Priority**: Implement Worker Dashboard
3. **Important**: Add role-based navigation
4. **Enhancement**: Optimize real-time updates

### **Need Help?**
- **API Questions**: Check the technical report for detailed API documentation
- **Implementation Issues**: Test API endpoints directly first
- **Design Questions**: Follow the UI specifications provided

---

## 🎉 **SUMMARY**

The backend warehouse worker functionality is **completely ready**. The frontend team needs to:

1. ✅ **Update existing Workers page** with new API calls
2. 🆕 **Create new Worker Dashboard** interface  
3. 🔄 **Implement role-based navigation** system
4. ⚡ **Add real-time updates** for live dashboard

**Estimated Frontend Work**: 2-3 days for full implementation
**Backend Status**: ✅ COMPLETE and PRODUCTION READY

The warehouse management system will be fully functional once these frontend updates are deployed!