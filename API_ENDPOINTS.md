# InternalOOX API Endpoints

## Base URL
- Production: `https://internaloox.onrender.com`
- Local Development: `http://localhost:8000`

## Authentication
- **Token Obtain**: `POST /api/token/`
- **Token Refresh**: `POST /api/token/refresh/`

## User Management
- **Users CRUD**: `/api/users/users/`
- **Login**: `POST /api/users/login/`
- **Logout**: `POST /api/users/logout/`
- **Current User**: `GET /api/users/current-user/`

## Orders Management
- **Customers**: `/api/customers/`
- **Orders**: `/api/orders/`
- **Payment Proofs**: `/api/payment-proofs/`
- **Order History**: `/api/order-history/`
- **Products**: `/api/products/`
- **Colors**: `/api/colors/`
- **Fabrics**: `/api/fabrics/`
- **Order Items**: `/api/order-items/`
- **Dashboard Stats**: `GET /api/dashboard-stats/`

## Admin Panel
- **Admin Interface**: `/admin/`

## Headers Required
```javascript
{
  'Content-Type': 'application/json',
  'Authorization': 'Bearer <your-jwt-token>'
}
```

## CORS Configuration
The backend is configured to accept requests from:
- Local development servers (localhost:3000, 3001, 8000)
- Any subdomain of onrender.com
- Your custom frontend domain (update in settings.py)