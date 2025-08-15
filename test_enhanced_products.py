#!/usr/bin/env python3
"""
Test script to verify enhanced color/fabric system is working
Run this from the backend directory: python test_enhanced_products.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oox_system.settings')
django.setup()

from orders.models import Product, Color, Fabric
from orders.serializers import ProductSerializer
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

def test_enhanced_product_creation():
    """Test enhanced product creation with colors and fabrics"""
    print("🧪 Testing Enhanced Product Creation...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'role': 'warehouse', 'is_active': True}
    )
    
    # Get existing colors and fabrics
    colors = Color.objects.all()[:2]  # Get first 2 colors
    fabrics = Fabric.objects.all()[:2]  # Get first 2 fabrics
    
    if not colors.exists() or not fabrics.exists():
        print("❌ Need at least 2 colors and 2 fabrics to test")
        return
    
    test_data = {
        'name': 'Enhanced Test Couch',
        'description': 'A couch with multiple color/fabric options',
        'price': '2000.00',
        'currency': 'ZAR',
        'colors': [c.id for c in colors],
        'fabrics': [f.id for f in fabrics],
        'sku': 'ENHANCED-COUCH-001',
        'attributes': {'material': 'Premium Wood', 'style': 'Contemporary'}
    }
    
    print(f"📝 Test data: {test_data}")
    
    try:
        # Create API request context
        factory = APIRequestFactory()
        request = factory.post('/api/orders/products/', test_data, format='json')
        request.user = user
        
        # Test serializer
        serializer = ProductSerializer(data=test_data, context={'request': request})
        if serializer.is_valid():
            print("✅ Serializer validation passed!")
            
            # Create product
            product = serializer.save()
            print(f"✅ Product created successfully!")
            print(f"🆔 Product ID: {product.id}")
            print(f"📛 Product Name: {product.product_name}")
            print(f"💰 Price: R{product.unit_price}")
            
            # Check enhanced color/fabric system
            print(f"🎨 Available Colors: {product.available_colors}")
            print(f"🧵 Available Fabrics: {product.available_fabrics}")
            print(f"🎨 Active Colors: {product.get_active_colors()}")
            print(f"🧵 Active Fabrics: {product.get_active_fabrics()}")
            
            # Test color/fabric management methods
            print("\n🔧 Testing color/fabric management methods...")
            
            # Add a new color
            product.add_color("Purple", "PUR", "https://example.com/purple.jpg")
            print(f"➕ Added Purple color: {product.get_active_colors()}")
            
            # Add a new fabric
            product.add_fabric("Velvet", "VEL", "https://example.com/velvet.jpg")
            print(f"➕ Added Velvet fabric: {product.get_active_fabrics()}")
            
            # Test to_representation
            print("\n📊 Testing serializer response...")
            response_data = serializer.to_representation(product)
            print(f"🎨 Response colors: {response_data.get('colors')}")
            print(f"🧵 Response fabrics: {response_data.get('fabrics')}")
            
            # Clean up test product
            product.delete()
            print("🧹 Test product cleaned up")
            
        else:
            print("❌ Serializer validation failed!")
            print(f"🚫 Errors: {serializer.errors}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Enhanced product creation test completed!")

if __name__ == '__main__':
    test_enhanced_product_creation()
