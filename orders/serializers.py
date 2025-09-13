from rest_framework import serializers
from .models import Order, Customer, PaymentProof, PaymentTransaction, OrderHistory, Product, Color, Fabric, OrderItem, ColorReference, FabricReference
from users.serializers import UserSerializer
from decimal import Decimal
import mimetypes
import uuid
import time

class CustomerSerializer(serializers.ModelSerializer):
	class Meta:
		model = Customer
		fields = '__all__'
		read_only_fields = ['created_at', 'updated_at']

class PaymentProofSerializer(serializers.ModelSerializer):
	uploaded_by = UserSerializer(read_only=True)
	absolute_url = serializers.SerializerMethodField(read_only=True)
	content_type = serializers.SerializerMethodField(read_only=True)
	file_name = serializers.SerializerMethodField(read_only=True)
	
	class Meta:
		model = PaymentProof
		fields = '__all__'
		read_only_fields = ['uploaded_by', 'uploaded_at', 'absolute_url', 'content_type', 'file_name']
	
	def get_absolute_url(self, obj):
		try:
			if not obj.proof_image:
				return None
			request = self.context.get('request') if hasattr(self, 'context') else None
			url = obj.proof_image.url
			return request.build_absolute_uri(url) if request else url
		except Exception:
			return None
	
	def get_content_type(self, obj):
		try:
			name = getattr(obj.proof_image, 'name', '') or ''
			ctype, _ = mimetypes.guess_type(name)
			return ctype or 'application/octet-stream'
		except Exception:
			return 'application/octet-stream'
	
	def get_file_name(self, obj):
		try:
			return getattr(obj.proof_image, 'name', None)
		except Exception:
			return None


class PaymentTransactionSerializer(serializers.ModelSerializer):
	actor_user = UserSerializer(read_only=True)
	order_number = serializers.CharField(source='order.order_number', read_only=True)
	proof = PaymentProofSerializer(read_only=True)
	
	# Computed field for transaction amount display
	transaction_amount = serializers.SerializerMethodField()
	
	class Meta:
		model = PaymentTransaction
		fields = [
			'id', 'order', 'order_number', 'actor_user',
			'total_amount_delta', 'deposit_delta', 'balance_delta',
			'amount_delta', 'previous_balance', 'new_balance',
			'payment_method', 'payment_status', 'proof', 'notes', 'created_at',
			'transaction_amount'  # Include the computed field
		]
		read_only_fields = fields
	
	def get_transaction_amount(self, obj):
		"""Compute the actual transaction amount for display purposes"""
		# For status changes, show the actual amounts
		if obj.payment_status == 'deposit_paid':
			return float(obj.deposit_delta) if obj.deposit_delta else 0
		elif obj.payment_status == 'fully_paid':
			return float(obj.balance_delta) if obj.balance_delta else 0
		else:
			# For amount updates, show the amount delta (positive means outstanding reduced)
			return float(obj.amount_delta) if obj.amount_delta else 0

class OrderHistorySerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only=True)
	
	class Meta:
		model = OrderHistory
		fields = '__all__'
		read_only_fields = ['user', 'timestamp']

class OrderItemSerializer(serializers.ModelSerializer):
	# Ensure product name resolves correctly to Product.product_name
	product_name = serializers.SerializerMethodField(read_only=True)
	# Prefer enhanced code-based names on the model properties; fall back to legacy FKs
	color_name = serializers.SerializerMethodField(read_only=True)
	fabric_name = serializers.SerializerMethodField(read_only=True)
	# Useful for UI color swatch
	hex_color = serializers.SerializerMethodField(read_only=True)
	# Convenience for UI display
	total_price = serializers.SerializerMethodField(read_only=True)
	
	class Meta:
		model = OrderItem
		fields = [
			'id', 'order', 'product', 'quantity', 'unit_price',
			'assigned_fabric_letter', 'assigned_color_code', 'color', 'fabric', 'product_description',
			'product_name', 'color_name', 'fabric_name', 'hex_color', 'total_price'
		]

	def get_product_name(self, obj):
		try:
			return getattr(obj.product, 'product_name', None) or getattr(obj.product, 'name', None)
		except Exception:
			return None

	def get_color_name(self, obj):
		# Use enhanced property that resolves from ColorReference via assigned_color_code
		try:
			return obj.color_name
		except Exception:
			# Legacy fallback
			return getattr(getattr(obj, 'color', None), 'name', None)

	def get_fabric_name(self, obj):
		# Use enhanced property that resolves from FabricReference via assigned_fabric_letter
		try:
			return obj.fabric_name
		except Exception:
			# Legacy fallback
			return getattr(getattr(obj, 'fabric', None), 'name', None)

	def get_hex_color(self, obj):
		try:
			from .models import ColorReference
			if obj.assigned_color_code:
				ref = ColorReference.objects.filter(color_code=obj.assigned_color_code).first()
				return ref.hex_color if ref and getattr(ref, 'hex_color', None) else None
		except Exception:
			pass
		return None

	def get_total_price(self, obj):
		try:
			return float(obj.total_price)
		except Exception:
			return None

class OrderSerializer(serializers.ModelSerializer):
	customer = CustomerSerializer(read_only=True)
	customer_id = serializers.IntegerField(write_only=True, required=False)
	customer_update = serializers.DictField(write_only=True, required=False)  # For customer updates
	created_by = UserSerializer(read_only=True)
	assigned_to_warehouse = UserSerializer(read_only=True)
	assigned_to_delivery = UserSerializer(read_only=True)
	payment_proofs = PaymentProofSerializer(many=True, read_only=True)
	history = OrderHistorySerializer(many=True, read_only=True)
	items = OrderItemSerializer(many=True, read_only=True)
	# Add write-only items field for order creation
	items_data = serializers.ListField(write_only=True, required=False)
	# Order-level discount inputs (write-only)
	order_discount_percent = serializers.DecimalField(max_digits=7, decimal_places=2, required=False, write_only=True)
	order_discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, write_only=True, help_text='Final total amount after discount')
	total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
	balance_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
	
	class Meta:
		model = Order
		fields = '__all__'
		read_only_fields = [
			'order_number', 'created_by', 'created_at', 'updated_at'
		]
	
	def validate(self, attrs):
		# For updates, financial fields are optional
		if self.instance:  # update
			return attrs
		# For creation, allow totals to be computed from items and discounts in create()
		return attrs
	
	def create(self, validated_data):
		print("ORDER CREATE - validated_data:", validated_data)
		print("ORDER CREATE - initial_data:", self.initial_data)
		print("ORDER CREATE - context:", self.context)
		
		# Ensure total_amount, deposit_amount, balance_amount are Decimal
		for field in ['total_amount', 'deposit_amount', 'balance_amount']:
			if field in validated_data and validated_data[field] is not None:
				validated_data[field] = Decimal(str(validated_data[field]))
		
		# Handle date fields properly
		# If frontend sends expected_delivery_date, use it as delivery_deadline for new orders
		if 'expected_delivery_date' in validated_data:
			delivery_date = validated_data.pop('expected_delivery_date')
			print(f"ORDER CREATE - Processing delivery date: {delivery_date} (type: {type(delivery_date)})")
			if delivery_date:
				try:
					# Ensure it's a valid date string
					from datetime import datetime
					if isinstance(delivery_date, str):
						# Parse and validate the date string
						parsed_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
						validated_data['delivery_deadline'] = parsed_date
						print(f"ORDER CREATE - Successfully parsed delivery date: {parsed_date}")
					else:
						validated_data['delivery_deadline'] = delivery_date
				except ValueError as e:
					print(f"ORDER CREATE - Date parsing error: {e}")
					# Don't set the date if it's invalid
					pass
		
		# Get items data from validated_data, context, or initial_data
		items_data = validated_data.pop('items_data', None)
		if not items_data:
			# Try context
			items_data = self.context.get('items_data', None)
		if not items_data:
			# Try initial_data['items_data'] (frontend contract)
			items_data = self.initial_data.get('items_data', None)
		if not items_data:
			# Try initial_data['items'] (legacy fallback)
			items_data = self.initial_data.get('items', [])
		print("ORDER CREATE - items_data:", items_data)
		print("ORDER CREATE - items_data type:", type(items_data))
		print("ORDER CREATE - items_data length:", len(items_data) if items_data else 0)
		# Validate items_data structure
		if items_data:
			for i, item in enumerate(items_data):
				print(f"ORDER CREATE - Item {i}: {item}")
				print(f"ORDER CREATE - Item {i} keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
		
		# Apply item-level discounts and compute order totals if not provided
		from decimal import Decimal as _D
		computed_subtotal = _D('0')
		processed_items = []
		for item in (items_data or []):
			try:
				quantity = _D(str(item.get('quantity', 1)))
				base_unit_price = _D(str(item.get('unit_price', 0)))
				# Item-specific discounts
				disc_percent = item.get('discount_percent')
				disc_amount_final = item.get('discount_amount')  # Final per-unit price after discount
				effective_unit_price = base_unit_price
				if disc_amount_final not in [None, "", 0, 0.0]:
					effective_unit_price = _D(str(disc_amount_final))
				elif disc_percent not in [None, "", 0, 0.0]:
					p = _D(str(disc_percent))
					if p < 0:
						p = _D('0')
					if p > 100:
						p = _D('100')
					effective_unit_price = (base_unit_price * (_D('100') - p) / _D('100')).quantize(_D('0.01'))
				line_total = (effective_unit_price * quantity).quantize(_D('0.01'))
				computed_subtotal += line_total
				# Stash effective price for later creation
				item['_effective_unit_price'] = str(effective_unit_price)
			except Exception as e:
				print(f"ORDER CREATE - Discount compute error on item: {e}")
				# Fall back to provided values
				try:
					quantity = _D(str(item.get('quantity', 1)))
					base_unit_price = _D(str(item.get('unit_price', 0)))
					computed_subtotal += (base_unit_price * quantity)
					item['_effective_unit_price'] = str(base_unit_price)
				except Exception:
					pass
		
		# Order-level discounts
		order_discount_amount = self.initial_data.get('order_discount_amount')
		order_discount_percent = self.initial_data.get('order_discount_percent')
		computed_total = computed_subtotal
		if order_discount_amount not in [None, ""]:
			try:
				final_total = _D(str(order_discount_amount))
				if final_total >= 0:
					computed_total = final_total
			except Exception:
				pass
		elif order_discount_percent not in [None, "", 0, 0.0]:
			try:
				p = _D(str(order_discount_percent))
				if p < 0:
					p = _D('0')
				if p > 100:
					p = _D('100')
				computed_total = (computed_subtotal * (_D('100') - p) / _D('100')).quantize(_D('0.01'))
			except Exception:
				pass
		
		# Set totals if not provided
		if not validated_data.get('total_amount'):
			validated_data['total_amount'] = computed_total
		# Compute balance if not provided
		if not validated_data.get('balance_amount'):
			deposit = _D(str(validated_data.get('deposit_amount', 0) or 0))
			validated_data['balance_amount'] = (computed_total - deposit).quantize(_D('0.01'))

		validated_data.pop('items_data', None)
		# Remove write-only discount fields that don't exist on the model
		validated_data.pop('order_discount_percent', None)
		validated_data.pop('order_discount_amount', None)
		validated_data['created_by'] = self.context['request'].user
		order = super().create(validated_data)
		
		print(f"ORDER CREATE - Order created with ID: {order.id}")
		
		# Auto-calculate estimated_completion_date to 20 business days from creation
		from datetime import timedelta
		from django.utils import timezone
		
		business_days = 20
		current_date = timezone.now().date()
		while business_days > 0:
			current_date += timedelta(days=1)
			if current_date.weekday() < 5:  # Monday to Friday
				business_days -= 1
		order.estimated_completion_date = current_date
		order.save()
		
		# Create order items
		created_items = []
		for item_data in items_data:
			print("ORDER CREATE - Creating item:", item_data)
			try:
				# Resolve enhanced code-based assignments
				assigned_color_code = item_data.get('assigned_color_code') or item_data.get('color_code')
				assigned_fabric_letter = item_data.get('assigned_fabric_letter') or item_data.get('fabric_letter')
				color_fk_id = item_data.get('color')
				fabric_fk_id = item_data.get('fabric')

				print(f"ORDER CREATE - Color code: {assigned_color_code}, Fabric letter: {assigned_fabric_letter}")
				print(f"ORDER CREATE - Color FK: {color_fk_id}, Fabric FK: {fabric_fk_id}")

				# If frontend sent legacy numeric IDs from reference endpoints, map them to codes
				try:
					if not assigned_color_code and color_fk_id:
						# Try resolve to ColorReference id (new reference table)
						ref = ColorReference.objects.filter(id=color_fk_id).first()
						if ref:
							assigned_color_code = ref.color_code
							color_fk_id = None  # avoid invalid FK to legacy Color table
						else:
							# Try legacy Color table as fallback
							legacy_color = Color.objects.filter(id=color_fk_id).first()
							if legacy_color:
								# Map legacy color to reference code if possible
								ref = ColorReference.objects.filter(color_name__iexact=legacy_color.name).first()
								if ref:
									assigned_color_code = ref.color_code
								color_fk_id = None  # avoid invalid FK
				except Exception as e:
					print(f"ORDER CREATE - Error processing color: {e}")
					pass
				try:
					if not assigned_fabric_letter and fabric_fk_id:
						ref = FabricReference.objects.filter(id=fabric_fk_id).first()
						if ref:
							assigned_fabric_letter = ref.fabric_letter
							fabric_fk_id = None
						else:
							# Try legacy Fabric table as fallback
							legacy_fabric = Fabric.objects.filter(id=fabric_fk_id).first()
							if legacy_fabric:
								# Map legacy fabric to reference letter if possible
								ref = FabricReference.objects.filter(fabric_name__iexact=legacy_fabric.name).first()
								if ref:
									assigned_fabric_letter = ref.fabric_letter
								fabric_fk_id = None  # avoid invalid FK
				except Exception as e:
					print(f"ORDER CREATE - Error processing fabric: {e}")
					pass

				# Only set legacy FKs if they actually exist
				if color_fk_id and not Color.objects.filter(id=color_fk_id).exists():
					color_fk_id = None
				if fabric_fk_id and not Fabric.objects.filter(id=fabric_fk_id).exists():
					fabric_fk_id = None

				# Determine effective unit price if discount applied
				effective_unit_price = item_data.get('_effective_unit_price')
				if effective_unit_price is None:
					effective_unit_price = item_data.get('unit_price')
				
				# Create the OrderItem
				order_item = OrderItem.objects.create(
					order=order,
					product_id=item_data['product'],
					quantity=item_data['quantity'],
					unit_price=effective_unit_price,
					assigned_color_code=(assigned_color_code or ''),
					assigned_fabric_letter=(assigned_fabric_letter or ''),
					color_id=color_fk_id,
					fabric_id=fabric_fk_id,
					product_description=item_data.get('product_description', '')
				)
				
				created_items.append(order_item)
				print(f"ORDER CREATE - Successfully created OrderItem {order_item.id}")
				
			except Exception as e:
				print(f"ORDER CREATE - ERROR creating OrderItem: {e}")
				print(f"ORDER CREATE - Item data that failed: {item_data}")
				# Continue with other items instead of failing the entire order
				continue
		
		print("ORDER CREATE - Order created successfully with", len(created_items), "items")
		print("ORDER CREATE - Created item IDs:", [item.id for item in created_items])
		return order

	def update(self, instance, validated_data):
		print("ORDER UPDATE - initial_data:", self.initial_data)
		print("ORDER UPDATE - validated_data:", validated_data)
		print("ORDER UPDATE - initial_data keys:", list(self.initial_data.keys()))
		print("ORDER UPDATE - request.data:", self.context.get('request').data)
		
		# Update customer info if present - check multiple sources
		customer_data = None
		
		# Try customer_update field first
		if 'customer_update' in self.initial_data:
			customer_data = self.initial_data['customer_update']
			print("ORDER UPDATE - Found customer_update in initial_data")
		elif 'customer_update' in self.context.get('request').data:
			customer_data = self.context.get('request').data['customer_update']
			print("ORDER UPDATE - Found customer_update in request.data")
		elif 'customer' in self.initial_data:
			customer_data = self.initial_data['customer']
			print("ORDER UPDATE - Found customer in initial_data")
		elif 'customer' in self.context.get('request').data:
			customer_data = self.context.get('request').data['customer']
			print("ORDER UPDATE - Found customer in request.data")
		
		# If still no customer data, try to get it from validated_data
		if not customer_data and 'customer_update' in validated_data:
			customer_data = validated_data.pop('customer_update')
			print("ORDER UPDATE - Found customer_update in validated_data")
		elif not customer_data and 'customer_data' in validated_data:
			customer_data = validated_data.pop('customer_data')
			print("ORDER UPDATE - Found customer_data in validated_data")
		elif not customer_data and 'customer_data' in self.initial_data:
			customer_data = self.initial_data['customer_data']
			print("ORDER UPDATE - Found customer_data in initial_data")
		
		print("ORDER UPDATE - customer_data:", customer_data)
		
		if customer_data:
			customer = instance.customer
			print("ORDER UPDATE - Updating customer fields:", list(customer_data.keys()))
			for field, value in customer_data.items():
				if hasattr(customer, field) and field != 'id':  # Don't update the ID
					setattr(customer, field, value)
					print(f"ORDER UPDATE - Set {field} = {value}")
			customer.save()
			print("ORDER UPDATE - Customer updated successfully")
		else:
			print("ORDER UPDATE - No customer data found in any source")

		# Update order fields
		for attr, value in validated_data.items():
			if attr not in ['items', 'items_data', 'customer_id']:
				setattr(instance, attr, value)
		instance.save()

		# Update order items
		items_data = self.context.get('items_data', self.initial_data.get('items', []))
		existing_items = {item.id: item for item in instance.items.all()}
		sent_item_ids = set()
		for item_data in items_data:
			item_id = item_data.get('id')
			# Resolve enhanced code-based assignments and validate legacy FKs
			assigned_color_code = item_data.get('assigned_color_code') or item_data.get('color_code')
			assigned_fabric_letter = item_data.get('assigned_fabric_letter') or item_data.get('fabric_letter')
			color_fk_id = item_data.get('color')
			fabric_fk_id = item_data.get('fabric')
			try:
				if not assigned_color_code and color_fk_id:
					ref = ColorReference.objects.filter(id=color_fk_id).first()
					if ref:
						assigned_color_code = ref.color_code
						color_fk_id = None
					else:
						# Try legacy Color table as fallback
						legacy_color = Color.objects.filter(id=color_fk_id).first()
						if legacy_color:
							# Map legacy color to reference code if possible
							ref = ColorReference.objects.filter(color_name__iexact=legacy_color.name).first()
							if ref:
								assigned_color_code = ref.color_code
							color_fk_id = None  # avoid invalid FK
			except Exception:
				pass
			try:
				if not assigned_fabric_letter and fabric_fk_id:
					ref = FabricReference.objects.filter(id=fabric_fk_id).first()
					if ref:
						assigned_fabric_letter = ref.fabric_letter
						fabric_fk_id = None
					else:
						# Try legacy Fabric table as fallback
						legacy_fabric = Fabric.objects.filter(id=fabric_fk_id).first()
						if legacy_fabric:
							# Map legacy fabric to reference letter if possible
							ref = FabricReference.objects.filter(fabric_name__iexact=legacy_fabric.name).first()
							if ref:
								assigned_fabric_letter = ref.fabric_letter
							fabric_fk_id = None  # avoid invalid FK
			except Exception:
				pass
			if color_fk_id and not Color.objects.filter(id=color_fk_id).exists():
				color_fk_id = None
			if fabric_fk_id and not Fabric.objects.filter(id=fabric_fk_id).exists():
				fabric_fk_id = None

			if item_id and item_id in existing_items:
				# Update existing item
				item = existing_items[item_id]
				item.product_id = item_data['product']
				item.quantity = item_data['quantity']
				item.unit_price = item_data['unit_price']
				item.assigned_color_code = (assigned_color_code or '')
				item.assigned_fabric_letter = (assigned_fabric_letter or '')
				item.color_id = color_fk_id
				item.fabric_id = fabric_fk_id
				item.save()
				sent_item_ids.add(item_id)
			else:
				# Create new item
				OrderItem.objects.create(
					order=instance,
					product_id=item_data['product'],
					quantity=item_data['quantity'],
					unit_price=item_data['unit_price'],
					assigned_color_code=(assigned_color_code or ''),
					assigned_fabric_letter=(assigned_fabric_letter or ''),
					color_id=color_fk_id,
					fabric_id=fabric_fk_id
				)
		# Delete items not in the update payload
		for item_id, item in existing_items.items():
			if item_id not in sent_item_ids:
				item.delete()
		return instance

class OrderListSerializer(serializers.ModelSerializer):
	customer = CustomerSerializer(read_only=True)
	customer_name = serializers.CharField(read_only=True)
	
	class Meta:
		model = Order
		fields = [
			'id', 'order_number', 'customer', 'customer_name',
			'order_date', 'expected_delivery_date', 'delivery_deadline',
			'order_status', 'production_status', 'payment_status',
			'deposit_amount', 'balance_amount', 'total_amount',
			'admin_notes', 'warehouse_notes', 'delivery_notes',
			'created_at', 'updated_at',
			# New queue management fields
			'deposit_paid_date', 'queue_position', 'is_priority_order',
			'production_start_date', 'estimated_completion_date'
		]

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Order
		fields = ['order_status', 'warehouse_notes', 'delivery_notes']
	
	def update(self, instance, validated_data):
		# Create history entry
		OrderHistory.objects.create(
			order=instance,
			user=self.context['request'].user,
			action=f"Status updated to {validated_data.get('order_status', instance.order_status)}",
			details=f"Updated by {self.context['request'].user.username}"
		)
		return super().update(instance, validated_data) 

class ProductSerializer(serializers.ModelSerializer):
	# Write-only fields from frontend contract
	price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
	currency = serializers.CharField(write_only=True, required=False, default='ZAR')
	color = serializers.CharField(write_only=True, required=False, allow_blank=True)
	fabric = serializers.CharField(write_only=True, required=False, allow_blank=True)
	colors = serializers.ListField(child=serializers.CharField(allow_blank=False), write_only=True, required=False, allow_empty=True)
	fabrics = serializers.ListField(child=serializers.CharField(allow_blank=False), write_only=True, required=False, allow_empty=True)
	sku = serializers.CharField(write_only=True, required=False, allow_blank=True)
	attributes = serializers.JSONField(required=False)

	# Make model-required fields optional at serializer layer
	product_type = serializers.CharField(required=False)
	product_name = serializers.CharField(required=False)
	default_fabric_letter = serializers.CharField(required=False)
	default_color_code = serializers.CharField(required=False)
	unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
	unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
	estimated_build_time = serializers.IntegerField(required=False)

	# Read-only aliased fields in responses
	created_at = serializers.DateTimeField(read_only=True)
	colors = serializers.ListField(child=serializers.CharField(), read_only=True)
	fabrics = serializers.ListField(child=serializers.CharField(), read_only=True)

	# Derived fields for image exposure without raw bytes
	main_image_url = serializers.SerializerMethodField(read_only=True)
	main_image_size = serializers.SerializerMethodField(read_only=True)
	main_image_present = serializers.SerializerMethodField(read_only=True)

	class Meta:
		model = Product
		fields = '__all__'
		read_only_fields = ['main_image']

	def validate(self, attrs):
		# Map name to product_name
		name = attrs.get('name') or attrs.get('product_name') or self.initial_data.get('name')
		if name:
			attrs['product_name'] = name
			attrs['name'] = name
		# Unit price from price
		if 'price' in self.initial_data and self.initial_data.get('price') not in [None, ""]:
			attrs['unit_price'] = Decimal(str(self.initial_data.get('price')))
		elif 'unit_price' in attrs and attrs['unit_price'] is not None:
			attrs['unit_price'] = Decimal(str(attrs['unit_price']))
		# Defaults for required fields
		attrs.setdefault('product_type', 'single')
		attrs.setdefault('unit_cost', Decimal('0'))
		attrs.setdefault('estimated_build_time', 1)
		fabric_name = self.initial_data.get('fabric') or attrs.get('fabric') or ''
		attrs.setdefault('default_fabric_letter', (fabric_name[:1].upper() if fabric_name else 'A'))
		attrs.setdefault('default_color_code', '01')
		# Model code from sku
		sku_value = self.initial_data.get('sku') or attrs.get('sku')
		if sku_value:
			attrs['model_code'] = sku_value
		# Attributes passthrough
		if 'attributes' in self.initial_data and isinstance(self.initial_data.get('attributes'), dict):
			attrs['attributes'] = self.initial_data.get('attributes')
		return attrs

	def create(self, validated_data):
		# Extract write-only contract fields
		price = Decimal(str(validated_data.pop('price', validated_data.get('unit_price', 0) or 0)))
		currency = validated_data.pop('currency', 'ZAR')
		color_name = validated_data.pop('color', '').strip() if 'color' in validated_data else (self.initial_data.get('color', '').strip() if hasattr(self, 'initial_data') else '')
		fabric_name = validated_data.pop('fabric', '').strip() if 'fabric' in validated_data else (self.initial_data.get('fabric', '').strip() if hasattr(self, 'initial_data') else '')
		color_list = validated_data.pop('colors', self.initial_data.get('colors', []) if hasattr(self, 'initial_data') else []) or []
		fabric_list = validated_data.pop('fabrics', self.initial_data.get('fabrics', []) if hasattr(self, 'initial_data') else []) or []
		sku = validated_data.pop('sku', '').strip() if 'sku' in validated_data else (self.initial_data.get('sku', '').strip() if hasattr(self, 'initial_data') else '')
		attributes = validated_data.pop('attributes', validated_data.get('attributes', None))

		# Auto-generate SKU if not provided
		if not sku:
			sku = f"OOX-{uuid.uuid4().hex[:8].upper()}-{int(time.time()) % 10000:04d}"

		# Ensure final mappings already handled in validate; just enforce unit_price
		validated_data['unit_price'] = price
		if sku and not validated_data.get('model_code'):
			validated_data['model_code'] = sku
		if attributes is not None:
			validated_data['attributes'] = attributes

		# Create product
		product = super().create(validated_data)

		# Use new enhanced color/fabric system with JSON fields
		# Build unique sets from singletons + arrays
		color_values = {v.strip() for v in ([color_name] if color_name else []) + list(color_list) if isinstance(v, str) and v.strip()}
		fabric_values = {v.strip() for v in ([fabric_name] if fabric_name else []) + list(fabric_list) if isinstance(v, str) and v.strip()}
		
		# Handle numeric color/fabric IDs from frontend
		if color_list and all(isinstance(c, (int, float)) for c in color_list):
			# Frontend sent numeric IDs, fetch color names
			try:
				color_objects = Color.objects.filter(id__in=color_list)
				color_values.update([c.name for c in color_objects])
			except Exception as e:
				print(f"Error fetching colors by ID: {e}")
		
		if fabric_list and all(isinstance(f, (int, float)) for f in fabric_list):
			# Frontend sent numeric IDs, fetch fabric names
			try:
				fabric_objects = Fabric.objects.filter(id__in=fabric_list)
				fabric_values.update([f.name for f in fabric_objects])
			except Exception as e:
				print(f"Error fetching fabrics by ID: {e}")
		
		# Store colors and fabrics in the new JSON fields
		if color_values:
			product.available_colors = [
				{'name': color_name, 'code': color_name.lower().replace(' ', '_'), 'is_active': True}
				for color_name in color_values if color_name
			]
		
		if fabric_values:
			product.available_fabrics = [
				{'name': fabric_name, 'code': fabric_name.lower().replace(' ', '_'), 'is_active': True}
				for fabric_name in fabric_values if fabric_name
			]
		
		# Save the updated product with colors/fabrics
		product.save()

		# Attach currency and echo fields for response
		self._response_currency = currency
		self._response_colors = list(color_values)
		self._response_fabrics = list(fabric_values)
		self._response_sku = sku
		self._response_price = price
		self._response_attributes = attributes
		return product

	def update(self, instance, validated_data):
		# Allow price via aliased field
		if hasattr(self, 'initial_data') and 'price' in self.initial_data and self.initial_data.get('price') not in [None, ""]:
			validated_data['unit_price'] = Decimal(str(self.initial_data.get('price')))

		# Extract aliased write-only fields similarly to create()
		color_name = (self.initial_data.get('color') or '').strip() if hasattr(self, 'initial_data') else ''
		fabric_name = (self.initial_data.get('fabric') or '').strip() if hasattr(self, 'initial_data') else ''
		color_list = (self.initial_data.get('colors', []) if hasattr(self, 'initial_data') else []) or []
		fabric_list = (self.initial_data.get('fabrics', []) if hasattr(self, 'initial_data') else []) or []

		# Build unique sets from singletons + arrays
		color_values = {v.strip() for v in (([color_name] if color_name else []) + list(color_list)) if isinstance(v, str) and v.strip()}
		fabric_values = {v.strip() for v in (([fabric_name] if fabric_name else []) + list(fabric_list)) if isinstance(v, str) and v.strip()}

		# Resolve numeric IDs to names if needed
		if color_list and all(isinstance(c, (int, float)) for c in color_list):
			try:
				color_objects = Color.objects.filter(id__in=color_list)
				color_values.update([c.name for c in color_objects])
			except Exception:
				pass
		if fabric_list and all(isinstance(f, (int, float)) for f in fabric_list):
			try:
				fabric_objects = Fabric.objects.filter(id__in=fabric_list)
				fabric_values.update([f.name for f in fabric_objects])
			except Exception:
				pass

		# Apply standard field updates first
		instance = super().update(instance, validated_data)

		# If aliased fields were provided, update JSON storage
		if color_values:
			instance.available_colors = [
				{'name': n, 'code': n.lower().replace(' ', '_'), 'is_active': True}
				for n in color_values if n
			]
		if fabric_values:
			instance.available_fabrics = [
				{'name': n, 'code': n.lower().replace(' ', '_'), 'is_active': True}
				for n in fabric_values if n
			]
		if color_values or fabric_values:
			instance.save()

		# Echo for response where applicable
		if color_values:
			self._response_colors = list(color_values)
		if fabric_values:
			self._response_fabrics = list(fabric_values)
		if hasattr(self, 'initial_data') and 'price' in self.initial_data:
			self._response_price = Decimal(str(self.initial_data.get('price')))

		return instance

	def to_representation(self, instance):
		data = super().to_representation(instance)
		# Expose image URL info for frontend; raw bytes are hidden
		data['main_image_url'] = self.get_main_image_url(instance)
		data['main_image_size'] = self.get_main_image_size(instance)
		data['main_image_present'] = self.get_main_image_present(instance)
		# Ensure raw bytes field is not present in payload
		if 'main_image' in data:
			del data['main_image']
		# Map fields back to frontend contract
		data.setdefault('name', instance.product_name or instance.name)
		data['price'] = str(self._response_price) if hasattr(self, '_response_price') else str(instance.unit_price or instance.base_price or 0)
		data['currency'] = getattr(self, '_response_currency', 'ZAR')
		# sku alias
		data['sku'] = getattr(self, '_response_sku', instance.model_code or '')
		# attributes
		data['attributes'] = instance.attributes or getattr(self, '_response_attributes', {}) or {}
		# Try fetch colors/fabrics from new JSON fields or response cache
		colors_list = getattr(self, '_response_colors', None)
		fabrics_list = getattr(self, '_response_fabrics', None)
		
		# If not in response cache, get from new JSON fields
		if colors_list is None:
			colors_list = instance.get_active_colors() if hasattr(instance, 'get_active_colors') else []
		if fabrics_list is None:
			fabrics_list = instance.get_active_fabrics() if hasattr(instance, 'get_active_fabrics') else []
		
		data['colors'] = colors_list or []
		data['fabrics'] = fabrics_list or []

		# Hide duplicated storage fields to reduce payload
		if 'available_colors' in data:
			del data['available_colors']
		if 'available_fabrics' in data:
			del data['available_fabrics']
		return data

	def get_main_image_present(self, instance):
		try:
			return bool(getattr(instance, 'main_image', None))
		except Exception:
			return False

	def get_main_image_size(self, instance):
		try:
			blob = getattr(instance, 'main_image', None)
			return len(blob) if blob else 0
		except Exception:
			return 0

	def get_main_image_url(self, instance):
		try:
			request = self.context.get('request') if hasattr(self, 'context') else None
			if not getattr(instance, 'main_image', None):
				return None
			from django.urls import reverse
			url_path = reverse('orders:product-main-image', kwargs={'pk': instance.pk})
			return request.build_absolute_uri(url_path) if request else url_path
		except Exception:
			return None

class ColorSerializer(serializers.ModelSerializer):
	class Meta:
		model = Color
		fields = '__all__'

class FabricSerializer(serializers.ModelSerializer):
	class Meta:
		model = Fabric
		fields = '__all__'

# MVP Reference Serializers
class ColorReferenceSerializer(serializers.ModelSerializer):
	class Meta:
		model = ColorReference
		fields = '__all__'

class FabricReferenceSerializer(serializers.ModelSerializer):
	class Meta:
		model = FabricReference
		fields = '__all__' 