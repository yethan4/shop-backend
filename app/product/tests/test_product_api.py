"""
Tests for the product API
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from product.models import Product, Category

PRODUCT_LIST_URL = reverse('product-list')


def product_detail_url(product_id):
    return reverse('product-detail', args=[product_id])


def create_category(name='default'):
    return Category.objects.create(name=name)


def create_product(**params):
    defaults = {
        'name': 'Product 1',
        'description': 'Description 1',
        'price': Decimal('10.50'),
        'stock': 100,
        'average_rating': 4.5,
        'ratings_count': 10,
        'category': None,
    }
    defaults.update(params)
    return Product.objects.create(**defaults)


class PublicProductAPITests(TestCase):
    """Tests for unauthenticated users"""

    def setUp(self):
        self.client = APIClient()
        self.category = create_category('Electronics')

    def test_retrieve_product_list(self):
        """Anonymous user can retrieve product list"""
        create_product(category=self.category)
        create_product(category=self.category)

        res = self.client.get(PRODUCT_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_retrieve_product_detail(self):
        """Anonymous user can retrieve product detail"""
        product = create_product(category=self.category, name="Phone")

        res = self.client.get(product_detail_url(product.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], product.name)

    def test_filter_product_by_category(self):
        """Anonymous user can filter products by category"""
        cat1 = create_category(name='Laptops')
        cat2 = create_category(name='Smartphones')

        prod1 = create_product(name='Laptop', category=cat1)
        prod2 = create_product(name='Smartphone', category=cat2)

        res = self.client.get(PRODUCT_LIST_URL, {'category': cat1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_names = [p['name'] for p in res.data]
        self.assertIn(prod1.name, returned_names)
        self.assertNotIn(prod2.name, returned_names)


class PrivateProductAPITests(TestCase):
    """Tests for authenticated users"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='janek123',
            email='user@example.com',
            first_name='Jan',
            last_name='Kowalski',
            phone_number='123456789',
            password='Test1234',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.category = create_category('Electronics')

    def test_retrieve_product_list_authenticated(self):
        """Authenticated user can retrieve product list"""
        create_product(category=self.category)
        create_product(category=self.category)

        res = self.client.get(PRODUCT_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_retrieve_product_detail_authenticated(self):
        """Authenticated user can retrieve product detail"""
        product = create_product(category=self.category, name="Laptop")

        res = self.client.get(product_detail_url(product.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], product.name)

    def test_filter_product_by_category_authenticated(self):
        """Authenticated user can filter products by category"""
        cat1 = create_category(name='Laptops')
        cat2 = create_category(name='Smartphones')

        prod1 = create_product(name='Laptop', category=cat1)
        prod2 = create_product(name='Smartphone', category=cat2)

        res = self.client.get(PRODUCT_LIST_URL, {'category': cat1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_names = [p['name'] for p in res.data]
        self.assertIn(prod1.name, returned_names)
        self.assertNotIn(prod2.name, returned_names)
