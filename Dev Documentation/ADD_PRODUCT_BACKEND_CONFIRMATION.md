# Add Product Backend Confirmation

This document confirms backend alignment for the Warehouse Manager Add Product feature for pilot testing.

## Endpoint
- POST `/api/products/`
- GET `/api/colors/`, GET `/api/fabrics/` for dropdowns

## Auth & Roles
- Auth: Bearer JWT
- Create permissions: `owner`, `admin`, `warehouse_manager`, `warehouse`
- Read: open (no auth required)

## Request (accepted)
```
{
  "name": "L-Shaped Couch",
  "sku": "OOX-LC-001",
  "description": "Modern L-shaped couch with storage",
  "price": 12999.99,
  "currency": "ZAR",
  "color": "Charcoal Gray",
  "fabric": "Suede",
  "attributes": { "Wood Type": "Oak", "Leg Color": "Black" }
}
```
Notes:
- `price` is saved to `unit_price`.
- `sku` is saved to `model_code`.
- `attributes` are stored in `Product.attributes` (JSONField).
- `color`/`fabric` labels are accepted and recorded via `ProductOption` entries and/or simple tables.

## Response (201)
```
{
  "id": 123,
  "name": "L-Shaped Couch",
  "sku": "OOX-LC-001",
  "description": "Modern L-shaped couch with storage",
  "price": "12999.99",
  "currency": "ZAR",
  "color": "Charcoal Gray",
  "fabric": "Suede",
  "attributes": { "Wood Type": "Oak", "Leg Color": "Black" },
  "created_at": "2025-08-10T12:34:56Z"
}
```

## Errors
- 400 validation: `{ "error": "<message>" }` or `{ "field": ["error1", ...] }`
- 403 permission denied for unauthorized roles

## Implementation Notes
- Model: `orders.Product` gained `attributes = models.JSONField(default=dict, null=True, blank=True)`
- Serializer: Maps frontend fields to model, persists color/fabric options, echoes currency
- Permissions: Custom `CanCreateProducts` enforces role-based create/update/delete

Ready for pilot. Any changes (IDs vs labels) can be supported with minor serializer adjustments.