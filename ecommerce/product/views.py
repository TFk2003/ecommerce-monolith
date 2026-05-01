from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

from ecommerce.product.models import Product
from ecommerce.product.serializers import ProductSerializer, ProductDetailSerializer, ProductImageSerializer
from ecommerce.permissions import IsSellerOrAdmin

logger = logging.getLogger(__name__)


class ProductCreateView(GenericAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsSellerOrAdmin]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_data['seller'] = request.user
        instance = serializer.create(validated_data)

        return Response(data=ProductDetailSerializer(instance).data, status=status.HTTP_201_CREATED)

    def patch(self, request, id=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
 
        validated_data = serializer.validated_data
        instance = Product.objects.get(id=id)
        instance = serializer.update(instance, validated_data)
 
        return Response(data=ProductDetailSerializer(instance).data, status=status.HTTP_200_OK)

    def delete(self, request, id=None):
        product_to_delete = Product.objects.get(id=id)
        product_to_delete.delete()

        queryset = Product.objects.all()

        return Response(ProductDetailSerializer(queryset, read_only=True, many=True).data, status=status.HTTP_200_OK)


class ProductDetailView(GenericAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, id=None):
        serializer = self.get_serializer_class()
        instance = Product.objects.get(id=id)
        return Response(serializer(instance).data, status=status.HTTP_200_OK)


class ProductListView(GenericAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        search = request.query_params.get('search')
        page = request.query_params.get('page')
        limit = request.query_params.get('limit')

        if search is None:
            search = ''

        if limit is None:
            limit = 4

        serializer = self.get_serializer_class()
        queryset = self.get_queryset()
        queryset = queryset.filter(name__icontains=search)
        paginator = Paginator(queryset, limit)

        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)

        if page is None:
            page = 1

        page = int(page)

        response = {
            'products': serializer(queryset, read_only=True, many=True).data,
            'page': page,
            'pages': paginator.num_pages
        }

        return Response(response, status=status.HTTP_200_OK)


class ProductListTopView(GenericAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = request.query_params.get('limit', 5)
        limit = int(limit)

        serializer_class = self.get_serializer_class()
        queryset = self.get_queryset()
        queryset = queryset.filter(rating__gte=4).order_by('-rating')[0:limit]

        return Response(serializer_class(queryset, many=True).data, status=status.HTTP_200_OK)


class ProductImageView(GenericAPIView):
    serializer_class = ProductImageSerializer
    permission_classes = [IsSellerOrAdmin]

    def post(self, request, id=None):
        serializer_instance = self.get_serializer_class()
        serializer = serializer_instance(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        print(validated_data)
        instance = Product.objects.get(id=id)
        instance.image = validated_data['image']
        instance.save()

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)


