#!/usr/bin/env python
"""
Simple test script to verify API endpoints are working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oox_system.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient

def test_endpoints():
    """Test the API endpoints"""
    client = APIClient()
    
    print("Testing API endpoints...")
    
    # Test products endpoint
    try:
        response = client.get('/api/orders/products/')
        print(f"Products endpoint: {response.status_code} - {len(response.data.get('results', []))} products")
    except Exception as e:
        print(f"Products endpoint error: {e}")
    
    # Test color-references endpoint
    try:
        response = client.get('/api/orders/color-references/')
        print(f"Color-references endpoint: {response.status_code} - {len(response.data.get('results', []))} colors")
    except Exception as e:
        print(f"Color-references endpoint error: {e}")
    
    # Test fabric-references endpoint
    try:
        response = client.get('/api/orders/fabric-references/')
        print(f"Fabric-references endpoint: {response.status_code} - {len(response.data.get('results', []))} fabrics")
    except Exception as e:
        print(f"Fabric-references endpoint error: {e}")

if __name__ == '__main__':
    test_endpoints()
