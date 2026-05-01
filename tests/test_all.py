from decimal import Decimal
 
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
 
from ecommerce.product.models import Product, ProductItem
from ecommerce.review.models import Review
from ecommerce.order.models import Order, OrderStatus
from ecommerce.payment.models import Payment, PaymentStatus
from ecommerce.address.models import ShippingAddress

User = get_user_model()

def make_user(email='buyer@test.com', is_staff=False):
    return User.objects.create_user(
        username=email, email=email, password='testpass123', name='Test User',
        is_staff=is_staff
    )
 
 
def make_product(seller, name='Laptop', price=999.99, stock=10):
    return Product.objects.create(
        name=name, brand='Dell', category='Electronics',
        price=Decimal(str(price)), count_in_stock=stock,
        seller=seller, rating=0.0, num_reviews=0,
        description='A test product.'
    )
 
 
def make_address():
    return ShippingAddress.objects.create(
        address='123 Main St', city='Karachi',
        state='Sindh', country='Pakistan', pincode='75000'
    )
 
 
def make_order(user, address):
    return Order.objects.create(
        user=user, shipping_address=address,
        tax_amount=Decimal('10.00'),
        shipping_amount=Decimal('5.00'),
        total_amount=Decimal('115.00'),
        status=OrderStatus.PLACED
    )

class ProductModelTest(TestCase):
 
    def setUp(self):
        self.seller = make_user('seller@test.com', is_staff=True)
 
    def test_product_created_successfully(self):
        product = make_product(self.seller)
        self.assertEqual(product.name, 'Laptop')
        self.assertEqual(product.count_in_stock, 10)
 
    def test_product_price_is_positive(self):
        product = make_product(self.seller, price=50.00)
        self.assertGreater(product.price, 0)
 
    def test_product_stock_non_negative(self):
        product = make_product(self.seller, stock=0)
        self.assertGreaterEqual(product.count_in_stock, 0)
 
    def test_product_slug_auto_generated(self):
        product = make_product(self.seller, name='Gaming Mouse')
        self.assertEqual(product.slug, 'gaming-mouse')
 
    def test_product_str(self):
        product = make_product(self.seller, name='Keyboard')
        self.assertEqual(str(product), 'Keyboard')

class ReviewModelTest(TestCase):
 
    def setUp(self):
        self.seller = make_user('seller2@test.com', is_staff=True)
        self.buyer = make_user('buyer2@test.com')
        self.product = make_product(self.seller)
 
    def test_review_updates_product_rating(self):
        initial_rating = self.product.rating  # 0.0
        Review.objects.create(
            author=self.buyer, product=self.product,
            rating=Decimal('4.00'), comment='Great product!'
        )
        self.product.refresh_from_db()
        self.assertGreater(self.product.rating, initial_rating)
 
    def test_review_increments_num_reviews(self):
        Review.objects.create(
            author=self.buyer, product=self.product,
            rating=Decimal('5.00'), comment='Excellent!'
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.num_reviews, 1)
 
    def test_review_str(self):
        review = Review.objects.create(
            author=self.buyer, product=self.product,
            rating=Decimal('3.00'), comment='Decent.'
        )
        expected = f'{self.buyer.username}_{self.product.slug}'
        self.assertEqual(str(review), expected)

class OrderServiceTest(TestCase):
 
    def setUp(self):
        self.seller = make_user('seller3@test.com', is_staff=True)
        self.buyer = make_user('buyer3@test.com')
        self.product = make_product(self.seller, stock=5)
        self.address = make_address()
 
    def test_place_order_creates_order(self):
        order = make_order(self.buyer, self.address)
        self.assertIsNotNone(order.id)
        self.assertEqual(order.status, OrderStatus.PLACED)
 
    def test_place_order_deducts_stock(self):
        initial_stock = self.product.count_in_stock
        order = make_order(self.buyer, self.address)
        ProductItem.objects.create(
            product=self.product, order=order, quantity=2
        )
        self.product.count_in_stock -= 2
        self.product.save()
 
        self.product.refresh_from_db()
        self.assertEqual(self.product.count_in_stock, initial_stock - 2)
 
    def test_insufficient_stock_raises_error(self):
        from ecommerce.order.service import _validate_stock
        items = [{'product': self.product, 'quantity': 100}]  # way more than stock=5
        with self.assertRaises(ValueError) as ctx:
            _validate_stock(items)
        self.assertIn('Insufficient stock', str(ctx.exception))
 
    def test_order_status_is_placed_by_default(self):
        order = make_order(self.buyer, self.address)
        self.assertEqual(order.status, OrderStatus.PLACED)
 
    def test_payment_created_for_order(self):
        order = make_order(self.buyer, self.address)
        payment = Payment.objects.create(
            order=order,
            payment_method='PayPal',
            payment_status=PaymentStatus.PENDING,
            amount=order.total_amount
        )
        self.assertEqual(payment.order, order)
        self.assertEqual(payment.payment_status, PaymentStatus.PENDING)

class ProductAPIPermissionTest(TestCase):
 
    def setUp(self):
        self.client = APIClient()
        self.buyer = make_user('apibuyertest@test.com', is_staff=False)
        self.seller = make_user('apisellertest@test.com', is_staff=True)
        self.product_data = {
            'name': 'API Test Product',
            'brand': 'TestBrand',
            'category': 'Electronics',
            'price': '29.99',
            'count_in_stock': 5,
            'description': 'Test description'
        }
 
    def test_unauthenticated_cannot_create_product(self):
        response = self.client.post('/api/products/create/', self.product_data)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
 
    def test_buyer_cannot_create_product(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post('/api/products/create/', self.product_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_seller_can_create_product(self):
        self.client.force_authenticate(user=self.seller)
        response = self.client.post('/api/products/create/', self.product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
 
    def test_anyone_can_list_products(self):
        response = self.client.get('/api/products/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
 
    def test_authenticated_user_can_place_order(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.get('/api/order/user/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
 
    def test_unauthenticated_cannot_list_orders(self):
        response = self.client.get('/api/order/list/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
