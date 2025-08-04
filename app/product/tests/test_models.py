"""
Tests for Category, Product and ProductImage models
"""
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from product import models


def create_category(name='Electronics'):
    """Helper to create and return a category."""
    return models.Category.objects.create(name=name)


def create_product(
    category=None,
    name='Laptop',
    description='A fast laptop',
    price='2999.99',
    stock=100,
    average_rating=4.5,
    ratings_count=12
):
    """Helper to create and return a product."""
    if category is None:
        category = create_category()
    return models.Product.objects.create(
        category=category,
        name=name,
        description=description,
        price=price,
        stock=stock,
        average_rating=average_rating,
        ratings_count=ratings_count
    )


class CategoryModelTests(TestCase):
    """Tests for the Category model."""

    def test_create_category_successful(self):
        """Test creating a category."""
        category = create_category(name='Books')
        self.assertEqual(str(category), 'Books')


class ProductModelTests(TestCase):
    """Tests for the Product model."""

    def test_create_product_successful(self):
        """Test creating a product with required fields."""
        category = create_category()
        product = create_product(category=category)
        self.assertEqual(str(product), f"{product.name} - {product.price}")
        self.assertEqual(product.category, category)
        self.assertEqual(product.stock, 100)
        self.assertEqual(product.average_rating, 4.5)
        self.assertEqual(product.ratings_count, 12)

    def test_stock_cannot_be_negative(self):
        """Test that stock cannot be set to a negative value."""

        category = models.Category.objects.create(name="TestCat")
        product = models.Product(
            category=category,
            name="Test Product",
            description="desc",
            price=10.00,
            stock=-5,
            average_rating=4.0,
            ratings_count=0,
        )
        with self.assertRaises(ValidationError):
            product.full_clean()


class ProductImageModelTests(TestCase):
    """Tests for the ProductImage model."""

    def test_create_product_image_successful(self):
        """Test creating a ProductImage."""
        product = create_product()
        image = models.ProductImage.objects.create(
            product=product,
            image='uploads/product/test.jpg',
            alt_text='Test image',
        )

        self.assertEqual(image.product, product)
        self.assertEqual(image.alt_text, 'Test image')
        self.assertTrue(str(image.image).startswith('uploads/product/'))

    @patch('product.models.uuid.uuid4')
    def test_product_image_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location with UUID."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.product_image_file_path(None, 'example.jpg')

        expected_path = f'uploads/product/{uuid}.jpg'
        self.assertEqual(file_path, expected_path)
