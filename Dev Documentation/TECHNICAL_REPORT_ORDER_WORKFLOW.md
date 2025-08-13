# Technical Report: Enhanced Order Workflow System

## Overview
This document outlines the new order workflow system with automated queue management, priority escalation, and enhanced delivery date controls implemented in the backend.

## 🔄 Field Position Changes (Frontend Required)

### Current Layout
```
Expected Delivery Date *    |    Order Status
[yyyy/mm/dd]               |    [Pending ▼]
```

### New Required Layout
```
Order Status                |    Expected Delivery Date *
[Status Dropdown ▼]        |    [yyyy/mm/dd] (conditional)
```

**Action Required**: Swap the positions of these two fields in the UI.

---

## 📋 New Order Status Options (Frontend Required)

### Updated Status Dropdown Options

Replace the current order status options with:

```javascript
const ORDER_STATUS_OPTIONS = [
  { value: 'deposit_pending', label: 'Deposit Pending' },
  { value: 'deposit_paid', label: 'Deposit Paid - In Queue' },
  { value: 'order_ready', label: 'Order Ready' },
  { value: 'out_for_delivery', label: 'Out for Delivery' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'cancelled', label: 'Cancelled' }
];
```

### Updated Payment Status Options

```javascript
const PAYMENT_STATUS_OPTIONS = [
  { value: 'deposit_pending', label: 'Deposit Pending' },
  { value: 'deposit_paid', label: 'Deposit Paid' },
  { value: 'fully_paid', label: 'Fully Paid' },
  { value: 'overdue', label: 'Overdue' }
];
```

---

## 🎯 Business Logic Implementation (Frontend Required)

### 1. Conditional Delivery Date Field

The delivery date field behavior must change based on order status:

```javascript
function shouldDisableDeliveryDate(orderStatus) {
  // Disable delivery date for these statuses
  return ['deposit_pending', 'deposit_paid'].includes(orderStatus);
}

function canSetDeliveryDate(orderStatus) {
  // Only allow delivery date when order is ready
  return orderStatus === 'order_ready';
}
```

**Implementation:**
- When `order_status = 'deposit_pending'`: Delivery date field should be **disabled/grayed out**
- When `order_status = 'deposit_paid'`: Delivery date field should be **disabled/grayed out**
- When `order_status = 'order_ready'`: Delivery date field becomes **enabled** and **required**

### 2. Priority Escalation (Owner Only)

Add a priority escalation button for owners:

```javascript
// Only show for owners
function canEscalatePriority(userRole, orderStatus) {
  return userRole === 'owner' && ['deposit_paid', 'order_ready'].includes(orderStatus);
}
```

**UI Requirements:**
- Add "🚀 Escalate Priority" button next to order actions
- Only visible to users with `role: 'owner'`
- Only enabled for orders with status `deposit_paid` or `order_ready`

---

## 🛠 New API Endpoints

### 1. Escalate Priority
```
POST /api/orders/{id}/escalate_priority/
Authorization: Bearer {token}

Response:
{
  "message": "Order escalated to priority successfully",
  "queue_position": 1,
  "is_priority_order": true
}
```

### 2. Queue Status Dashboard
```
GET /api/orders/queue_status/

Response:
{
  "total_orders_in_queue": 5,
  "queue": [
    {
      "id": 1,
      "order_number": "OOX000001",
      "customer_name": "John Doe",
      "queue_position": 1,
      "deposit_paid_date": "2024-07-15T10:00:00Z",
      "days_in_queue": 5,
      "estimated_completion_date": "2024-08-10",
      "is_priority_order": true,
      "is_queue_expired": false
    }
  ]
}
```

### 3. Set Delivery Date
```
PATCH /api/orders/{id}/set_delivery_date/
Authorization: Bearer {token}

Body:
{
  "delivery_date": "2024-08-15"
}

Response:
{
  "message": "Delivery date set successfully",
  "expected_delivery_date": "2024-08-15"
}
```

---

## 📊 New Data Fields in Order Objects

When fetching orders, the following new fields are now available:

```javascript
{
  "id": 1,
  "order_number": "OOX000001",
  // ... existing fields ...
  
  // New queue management fields
  "deposit_paid_date": "2024-07-15T10:00:00Z",
  "queue_position": 3,
  "is_priority_order": false,
  "production_start_date": null,
  "estimated_completion_date": "2024-08-10"
}
```

### Field Descriptions:
- `deposit_paid_date`: When the deposit was paid (starts the 20-day queue timer)
- `queue_position`: Position in the production queue (1 = first in line)
- `is_priority_order`: Whether this order was escalated by owner
- `production_start_date`: When production actually started
- `estimated_completion_date`: Auto-calculated completion date (20 business days from deposit)

---

## 🏗 Recommended UI Components

### 1. Queue Dashboard Component
Create a new dashboard showing:
- Total orders in queue
- Queue position for each order
- Days spent in queue
- Estimated completion dates
- Priority status indicators

### 2. Status Update Component
Enhanced order status component with:
- Conditional delivery date field
- Status-based validation
- Progress indicators

### 3. Priority Management Component (Owner Only)
- Priority escalation button
- Queue position display
- Priority status badges

---

## ⚠️ Important Business Rules

### Automatic Behaviors (Handled by Backend)
1. **Deposit Paid → Queue**: When status changes to `deposit_paid`, order automatically enters queue
2. **Queue Position**: Automatically assigned based on order of deposit payment
3. **20-Day Timer**: Starts counting from `deposit_paid_date`
4. **Priority Escalation**: Moves order to position #1 in queue

### Frontend Validation Rules
1. **Delivery Date Validation**: Only allow setting when `order_status = 'order_ready'`
2. **Status Progression**: Implement logical status progression (can't go from delivered back to pending)
3. **Owner Permissions**: Priority escalation only for users with `role: 'owner'`

---

## 🚀 Implementation Checklist

### Phase 1: UI Changes
- [ ] Swap field positions (Status first, then Delivery Date)
- [ ] Update status dropdown options
- [ ] Implement conditional delivery date field
- [ ] Add status-based validation

### Phase 2: Queue Management
- [ ] Create queue dashboard component
- [ ] Add queue status indicators to order list
- [ ] Implement estimated completion date display

### Phase 3: Priority System
- [ ] Add priority escalation button (owner only)
- [ ] Implement priority status badges
- [ ] Add confirmation dialogs for escalation

### Phase 4: Enhanced UX
- [ ] Add progress indicators for queue status
- [ ] Implement status change notifications
- [ ] Add tooltips explaining business rules

---

## 💡 User Experience Guidelines

### Status Indicators
- 🟡 **Deposit Pending**: Waiting for customer payment
- 🟠 **Deposit Paid**: In production queue (show queue position)
- 🟢 **Order Ready**: Available for delivery scheduling
- 🚚 **Out for Delivery**: In transit
- ✅ **Delivered**: Completed

### Visual Cues
- **Disabled fields**: Gray out delivery date when status is pending/paid
- **Priority orders**: Add 🚀 icon or special border
- **Queue expired**: Red warning for orders > 20 days
- **Owner actions**: Different button color/style for owner-only features

---

## 📞 Backend Support

All backend logic is implemented and ready. The frontend team can:
1. Test all new endpoints immediately
2. Use the new fields in order objects
3. Implement the conditional logic as described

For questions or clarification, contact the backend team.

## 📝 Testing Scenarios

### Test Case 1: Normal Order Flow
1. Create order with status "Deposit Pending"
2. Verify delivery date is disabled
3. Change status to "Deposit Paid"
4. Verify order enters queue automatically
5. Change status to "Order Ready"
6. Verify delivery date becomes enabled

### Test Case 2: Priority Escalation (Owner Only)
1. Log in as owner
2. Find order with status "Deposit Paid"
3. Click "Escalate Priority"
4. Verify order moves to queue position #1

### Test Case 3: Queue Dashboard
1. Navigate to queue dashboard
2. Verify orders are sorted by queue position
3. Check estimated completion dates
4. Verify priority orders are highlighted

---

*This document serves as the complete technical specification for implementing the enhanced order workflow system. All backend functionality is complete and ready for frontend integration.*