from django.http import Http404
from requests import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.pagination import PageNumberPagination
from .models import Brand, Product, Category, SubCategory, Stock, Store, Packaging
from .serializers import (
    BrandSerializer,
    ProductSerializer,
    CategorySerializer,
    SubCategorySerializer,
    StockSerializer,
)
from authentication.permissions import IsStaffOrReadOnly
from rest_framework.generics import get_object_or_404
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        category_name = serializer.validated_data.get("name")
        if Category.objects.filter(name=category_name).exists():
            raise DRFValidationError(
                f"Category with name '{category_name}' already exists."
            )
        serializer.save()


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_update(self, serializer):
        category_instance = self.get_object()
        category_name = serializer.validated_data.get("name")
        if (
            Category.objects.filter(name=category_name)
            .exclude(id=category_instance.id)
            .exists()
        ):
            raise DRFValidationError(
                f"Category with name '{category_name}' already exists."
            )
        serializer.save()


class SubCategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        subcategory_name = serializer.validated_data.get("name")
        if SubCategory.objects.filter(name=subcategory_name).exists():
            raise DRFValidationError(
                f"SubCategory with name '{subcategory_name}' already exists."
            )
        serializer.save()


class SubCategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_update(self, serializer):
        subcategory_instance = self.get_object()
        subcategory_name = serializer.validated_data.get("name")
        if (
            SubCategory.objects.filter(name=subcategory_name)
            .exclude(id=subcategory_instance.id)
            .exists()
        ):
            raise DRFValidationError(
                f"SubCategory with name '{subcategory_name}' already exists."
            )
        serializer.save()


class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category__name", lookup_expr="icontains")
    subcategories = filters.CharFilter(method="filter_by_subcategories")
    brand = filters.CharFilter(
        field_name="brand__name", lookup_expr="icontains"
    )  # Correct filter for brand

    class Meta:
        model = Product
        fields = ["category", "subcategories", "brand"]

    def filter_by_subcategories(self, queryset, name, value):
        # Split the incoming value by commas and filter by each subcategory
        subcategory_names = value.split(",")
        for subcategory_name in subcategory_names:
            queryset = queryset.filter(subcategories__name__icontains=subcategory_name)
        return queryset.distinct()


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]  # Adjust permission as needed
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        category_name = self.request.query_params.get("category", None)
        subcategory_name = self.request.query_params.get("subcategory", None)
        brand_name = self.request.query_params.get("brand", None)

        if category_name:
            queryset = queryset.filter(category__name__icontains=category_name)

        if subcategory_name:
            queryset = queryset.filter(subcategories__name__icontains=subcategory_name)

        if brand_name:
            queryset = queryset.filter(brand__name__icontains=brand_name)

        # If user is not authenticated, exclude price by limiting fields
        if not self.request.user.is_authenticated:
            queryset = queryset.only(
                "product_id",
                "product_name",
                "description",
                "brand",
                "image1",
                "image2",
                "image3",
            )

        return queryset.distinct()  # Ensure distinct results

    def perform_create(self, serializer):
        self.validate_packaging(serializer)
        self.validate_product_uniqueness(serializer)
        serializer.save()
        product_id = serializer.validated_data.get("product_id")
        upc = serializer.validated_data.get("upc")

        if Product.objects.filter(product_id=product_id).exists():
            raise DRFValidationError(
                f"Product with product_id '{product_id}' already exists."
            )

        if upc and Product.objects.filter(upc=upc).exists():
            raise DRFValidationError(f"Product with UPC '{upc}' already exists.")


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_update(self, serializer):
        self.validate_packaging(serializer)
        self.validate_product_uniqueness(serializer)
        self.validate_images(serializer)
        serializer.save()

    def validate_images(self, serializer):
        """Validate image fields for update."""
        for field in ["image1", "image2", "image3"]:
            image = self.request.data.get(field, None)
            if image and not isinstance(image, UploadedFile):
                raise DRFValidationError(f"{field} must be a valid image file.")

    def validate_packaging(self, serializer):
        packaging_data = self.request.data.get("packaging", None)
        if packaging_data:
            packaging_quantity = packaging_data.get("packaging_quantity")
            packaging_value = packaging_data.get("packaging_value")
            packaging_type = packaging_data.get("packaging_type")
            if not packaging_quantity or not packaging_value or not packaging_type:
                raise DRFValidationError("All packaging fields must be provided.")
            packaging, created = Packaging.objects.get_or_create(
                packaging_quantity=packaging_quantity,
                packaging_value=packaging_value,
                packaging_type=packaging_type,
            )
            serializer.validated_data["packaging"] = packaging

    def validate_product_uniqueness(self, serializer):
        product_id = serializer.validated_data.get("product_id")
        upc = serializer.validated_data.get("upc")

        if Product.objects.filter(product_id=product_id).exists():
            raise DRFValidationError(
                f"Product with product_id '{product_id}' already exists."
            )
        if upc and Product.objects.filter(upc=upc).exists():
            raise DRFValidationError(f"Product with UPC '{upc}' already exists.")

        product_id = serializer.validated_data.get("product_id")
        upc = serializer.validated_data.get("upc")

        if Product.objects.filter(product_id=product_id).exists():
            raise DRFValidationError(
                f"Product with product_id '{product_id}' already exists."
            )
        if upc and Product.objects.filter(upc=upc).exists():
            raise DRFValidationError(f"Product with UPC '{upc}' already exists.")


class StockPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class StockListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StockPagination

    def get_queryset(self):
        try:
            # Retrieve the store using store_id from URL
            store_id = self.kwargs["store_id"]
            store = get_object_or_404(Store, store_id=store_id)
            return Stock.objects.filter(store=store)  # Filter stocks based on store_id
        except Store.DoesNotExist:
            # Handle the case where the store doesn't exist
            raise Http404(f"Store with ID {store_id} not found.")
        except Exception as e:
            # Catch other unexpected errors
            raise Http404(f"An unexpected error occurred: {str(e)}")

    def perform_create(self, serializer):
        try:
            store_id = self.kwargs["store_id"]
            store = get_object_or_404(Store, store_id=store_id)
            product = serializer.validated_data.get("product")

            # Check if a stock record already exists for the product and store
            if Stock.objects.filter(product=product, store=store).exists():
                raise DRFValidationError(
                    f"Stock record for product '{product.product_name}' at store '{store.name}' already exists."
                )

            # Save the new stock record
            serializer.save(store=store)

        except Store.DoesNotExist:
            # Handle the case where the store doesn't exist
            raise Http404(f"Store with ID {store_id} not found.")
        except DRFValidationError as e:
            # Handle validation error if stock already exists
            raise e  # Re-raise DRFValidationError to be handled by DRF
        except Exception as e:
            # Catch any other unexpected exceptions
            raise DRFValidationError(f"An error occurred while creating stock: {str(e)}")


class StockRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a Stock instance.
    """

    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter Stock objects by store_id and product_id from the URL path.
        """
        store_id = self.kwargs.get("store_id")
        product_id = self.kwargs.get("product_id")

        # Validate and retrieve store and product
        store = get_object_or_404(Store, store_id=store_id)
        product = get_object_or_404(Product, product_id=product_id)

        # Filter Stock based on store and product
        return Stock.objects.filter(store=store, product=product)

    def get_object(self):
        """
        Retrieve a single Stock object from the filtered queryset.
        """
        queryset = self.get_queryset()
        return get_object_or_404(queryset)

    def update(self, request, *args, **kwargs):
        """
        Override update method to handle validation and custom responses.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError as exc:
            # Return a custom error response on validation failure
            return Response(
                {
                    "errors": exc.detail,
                    "message": "Validation failed",
                    "status_code": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Perform the update
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Handle deletion of a Stock instance.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Stock deleted successfully", "status_code": 204},
            status=status.HTTP_204_NO_CONTENT,
        )

    def perform_update(self, serializer):
        """
        Save the updated Stock instance.
        """
        serializer.save()

    def perform_destroy(self, instance):
        """
        Delete the Stock instance.
        """
        instance.delete()


class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.all()  # Get all brands
    serializer_class = BrandSerializer  # Use the BrandSerializer for serializing data
    permission_classes = [IsStaffOrReadOnly]
