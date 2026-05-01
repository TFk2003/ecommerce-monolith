from django.db import transaction
 
from ecommerce.order.models import Order
from ecommerce.payment.models import Payment
from ecommerce.product.models import ProductItem
from ecommerce.address.models import ShippingAddress
 
 
def _validate_stock(product_items_data):
    """
    Check every item has sufficient stock before any DB write.
    Raises ValueError if any product is out of stock.
    """
    for item_data in product_items_data:
        product = item_data['product']
        quantity = item_data.get('quantity', 1)
        if product.count_in_stock < quantity:
            raise ValueError(
                f"Insufficient stock for '{product.name}'. "
                f"Requested: {quantity}, Available: {product.count_in_stock}"
            )
 
 
def _deduct_stock(product, quantity):
    """Reduce product stock by quantity and save."""
    product.count_in_stock -= quantity
    product.save(update_fields=['count_in_stock'])
 
 
def _create_shipping_address(address_data):
    """Create and return a ShippingAddress instance."""
    return ShippingAddress.objects.create(**address_data)
 
 
def _create_payment(payment_data, order):
    """Create a Payment record linked to the order."""
    payment = Payment.objects.create(**payment_data)
    payment.order = order
    payment.amount = order.total_amount
    payment.save()
    return payment
 
 
def _create_product_items(product_items_data, order):
    """Create all ProductItem records and deduct stock atomically."""
    for item_data in product_items_data:
        product = item_data['product']
        quantity = item_data.get('quantity', 1)
 
        item = ProductItem.objects.create(
            product=product,
            order=order,
            quantity=quantity,
            is_active=True,
        )
        _deduct_stock(product, quantity)
 
    return order
 
 
@transaction.atomic
def place_order(user, validated_data):
    """
    Main service function: place an order end-to-end.
 
    Steps:
      1. Validate stock for all items (fail fast before any writes)
      2. Create ShippingAddress
      3. Create Order
      4. Create Payment
      5. Create ProductItems + deduct stock
 
    All steps run inside a single DB transaction — if anything fails,
    everything is rolled back automatically.
 
    Args:
        user: The authenticated User placing the order.
        validated_data: Dict from OrderCreateSerializer.validated_data
 
    Returns:
        Order instance (fully created and saved)
 
    Raises:
        ValueError: if stock is insufficient for any item
    """
    # Pop nested data
    shipping_address_data = validated_data.pop('shipping_address')
    payment_data = validated_data.pop('order_payments')
    product_items_data = validated_data.pop('order_product_items')
 
    # Step 1: Validate stock BEFORE any writes
    _validate_stock(product_items_data)
 
    # Step 2: Create shipping address
    shipping_address_data['shipping_amount'] = validated_data.get('shipping_amount', 0)
    shipping_address = _create_shipping_address(shipping_address_data)
 
    # Step 3: Create order
    order = Order.objects.create(**validated_data)
    order.user = user
    order.shipping_address = shipping_address
    order.save()
 
    # Step 4: Create payment
    _create_payment(payment_data, order)
 
    # Step 5: Create product items and deduct stock
    _create_product_items(product_items_data, order)
 
    return order