from rest_framework import serializers

from ecommerce.product.models import Product, ProductItem
from ecommerce.review.models import Review
from ecommerce.user.serializers import UserSerializer


class ProductSerializer(serializers.ModelSerializer):
    
    def validate_price(self, value):
        """Price must be greater than zero."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
 
    def validate_count_in_stock(self, value):
        """Stock cannot be a negative number."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Stock count cannot be negative.")
        return value
 
    def validate_name(self, value):
        """Product name cannot be blank."""
        if not value or not value.strip():
            raise serializers.ValidationError("Product name cannot be blank.")
        return value
 
    def validate_category(self, value):
        """Category cannot be blank."""
        if not value or not value.strip():
            raise serializers.ValidationError("Category cannot be blank.")
        return value
    
    def find_by_slug(self, slug):
        instance = Product.objects.get(slug=slug)
        return instance

    class Meta:
        model = Product
        exclude = ('is_deleted',)
        extra_kwargs = {
            'image': {'required': False, 'allow_null': True},
            'name': {'required': False},
            'description': {'required': False},
            'price': {'required': False},
            'brand': {'required': False},
            'category': {'required': False},
            'count_in_stock': {'required': False},
        }


class ProductReviewSerializer(serializers.ModelSerializer):
    author = UserSerializer()

    class Meta:
        model = Review
        exclude = ('is_deleted', 'product',)


class ProductDetailSerializer(ProductSerializer):
    seller = UserSerializer()
    reviews = ProductReviewSerializer(source='product_reviews', many=True)

    def find_by_slug(self, slug):
        instance = Product.objects.get(slug=slug)
        return instance

    class Meta:
        model = Product
        exclude = ('is_deleted',)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'image',)


class ProductItemSerializer(serializers.ModelSerializer):
    def validate_quantity(self, value):
        """Quantity must be at least 1."""
        if value is not None and value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value
    
    def create(self, validated_data):
        product = validated_data.pop('product')
        quantity = validated_data.get('quantity', 0)
        if product.count_in_stock < quantity:
            raise serializers.ValidationError(
                f"Insufficient stock. Only {product.count_in_stock} unit(s) available."
            )
        
        product_item = super().create(validated_data)

        product.count_in_stock -= product_item.quantity
        print(product)
        # product.product_product_item.set(product)
        print(product.count_in_stock)
        product.save()

        product_item.product = product
        product_item.save()
        return product_item

    class Meta:
        model = ProductItem
        exclude = ('is_deleted',)


class ProductItemDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    product = ProductDetailSerializer()

    def get_name(self, instance):
        return instance.product.name

    def get_slug(self, instance):
        return instance.product.slug

    class Meta:
        model = ProductItem
        exclude = ('is_deleted',)
