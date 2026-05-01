from rest_framework import serializers

from ecommerce.address.serializers import ShippingAddressDetailSerializer, ShippingAddressSerializer
from ecommerce.order.models import Order
from ecommerce.order.service import place_order
from ecommerce.payment.serializers import PaymentSerializer
from ecommerce.product.serializers import ProductItemDetailSerializer, ProductItemSerializer
from ecommerce.user.serializers import UserSerializer


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, required=False)
    shipping_address = ShippingAddressDetailSerializer(many=False, required=False)
    payment = PaymentSerializer(many=False, required=False, source='order_payment')
    product_items = ProductItemDetailSerializer(many=True, required=False, source='order_product_items')

    def get_by_id(self, id):
        return Order.objects.get(id=id)

    def update(self, instance, validated_data):
        if 'shipping_address' in list(validated_data.keys()):
            shipping_address = validated_data.pop('shipping_address')
            shipping_instance = instance.shipping_address
            shipping_instance = ShippingAddressDetailSerializer().update(shipping_instance, shipping_address)
            instance.shipping_address = shipping_instance

        if 'order_payment' in list(validated_data.keys()):
            order_payment = validated_data.pop('order_payment')
            payment_instance = instance.order_payment
            payment_instance = PaymentSerializer().update(payment_instance, order_payment)
            instance.order_payment = payment_instance

        if 'order_product_items' in list(validated_data.keys()):
            validated_data.pop('order_product_items')
 
        instance = super().update(instance, validated_data)
        return instance


    class Meta:
        model = Order
        fields = ('id', 'user', 'product_items', 'payment', 'status', 'shipping_address', 'is_active', 'created',
                  'modified', 'tax_amount',  'total_amount', 'shipping_amount')


class OrderCreateSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(required=False)
    payment = PaymentSerializer(many=False, required=False, source='order_payments')
    product_items = ProductItemSerializer(many=True, required=False, source='order_product_items')

    def create(self, validated_data):
        user = self.context.get('request').user
        try:
            return place_order(user, validated_data)
        except ValueError as e:
            # Stock validation errors from service layer → return 400
            raise serializers.ValidationError(str(e))

    class Meta:
        model = Order
        exclude = ('is_deleted',)

