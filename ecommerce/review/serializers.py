from rest_framework import serializers

from ecommerce.product.serializers import ProductSerializer
from ecommerce.review.models import Review
from ecommerce.user.serializers import UserSerializer


class ReviewSerializer(serializers.ModelSerializer):

    def validate_rating(self, value):
        """Rating must be a decimal between 1.00 and 5.00."""
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
 
    def validate_comment(self, value):
        """Review comment cannot be blank or whitespace."""
        if not value or not value.strip():
            raise serializers.ValidationError("Review comment cannot be blank.")
        return value
    
    class Meta:
        model = Review
        fields = '__all__'


class ReviewDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    product = ProductSerializer()
 
    class Meta:
        model = Review
        fields = '__all__'
