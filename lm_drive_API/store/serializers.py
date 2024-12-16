import datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Category, SubCategory, Stock, Packaging, Brand


class BaseCategorySerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        # Try handling category by id or name.
        category = self._get_category(data)
        if category:
            return {"id": category.id, "name": category.name}
        raise ValidationError(
            f"{self.Meta.model.__name__} must have either an 'id' or 'name'."
        )

    def _get_category(self, data):
        """Helper method to fetch the category by either 'id' or 'name'."""
        category_id = data.get("id")
        category_name = data.get("name")

        if category_id:
            return self._get_category_by_id(category_id)
        if category_name:
            return self._get_category_by_name(category_name)
        return None

    def _get_category_by_id(self, category_id):
        """Helper method to fetch category by ID."""
        try:
            return self.Meta.model.objects.get(id=category_id)
        except self.Meta.model.DoesNotExist:
            raise ValidationError(
                f"{self.Meta.model.__name__} with ID '{category_id}' does not exist."
            )

    def _get_category_by_name(self, category_name):
        """Helper method to fetch category by name."""
        try:
            return self.Meta.model.objects.get(name=category_name)
        except self.Meta.model.DoesNotExist:
            return super().to_internal_value(
                {"name": category_name}
            )  # Let base method handle it


class CategorySerializer(BaseCategorySerializer):
    class Meta:
        model = Category
        fields = ["name"]


class SubCategorySerializer(BaseCategorySerializer):
    class Meta:
        model = SubCategory
        fields = ["name"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]  # Fields you want to include in the API response


class PackagingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packaging
        fields = [
            "packaging_quantity",
            "packaging_value",
            "packaging_type",
        ]


class ProductSerializer(serializers.ModelSerializer):
    brand = serializers.SlugRelatedField(
        queryset=Brand.objects.all(),
        slug_field="name",
    )
    category = CategorySerializer()
    subcategories = SubCategorySerializer(many=True)
    stock_summary = serializers.SerializerMethodField()
    stocks = serializers.SerializerMethodField()
    packaging = PackagingSerializer()
    price_ttc = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "product_id",
            "product_name",
            "upc",
            "description",
            "price_ht",
            "tva",
            "price_ttc",
            "is_for_sale",
            "brand",
            "category",
            "subcategories",
            "image1",
            "image2",
            "image3",
            "packaging",
            "stock_summary",
            "stocks",
        ]

    def to_representation(self, instance):
        """
        Customize representation to exclude sensitive fields for unauthenticated users.
        """
        representation = super().to_representation(instance)
        request = self.context.get("request")

        # Exclude sensitive fields for unauthenticated users
        if not (request and request.user.is_authenticated):
            representation.pop("price_ht", None)
            representation.pop("tva", None)
            representation.pop("price_ttc", None)

        # Add absolute URLs for images
        representation["image_urls"] = self.get_image_urls(instance)

        return representation

    def get_stock_summary(self, obj):
        """
        Retrieve the stock summary for a product.
        """
        return obj.get_stock_summary()

    def get_stocks(self, obj):
        """
        Fetch stock information for the product in a simplified format.
        """
        stock_queryset = obj.stocks.select_related("store")
        return [
            {
                "store": stock.store.store_id,
                "quantity": stock.quantity_in_stock,
                "expiration_date": stock.expiration_date,
            }
            for stock in stock_queryset
        ]

    def get_image_urls(self, obj):
        """
        Generate absolute URLs for product images.
        """
        request = self.context.get("request")
        image_urls = {}
        if request:
            if obj.image1:
                image_urls["image1"] = request.build_absolute_uri(obj.image1.url)
            if obj.image2:
                image_urls["image2"] = request.build_absolute_uri(obj.image2.url)
            if obj.image3:
                image_urls["image3"] = request.build_absolute_uri(obj.image3.url)
        return image_urls

    def create(self, validated_data):
        """
        Create a new product with nested relationships.
        """
        packaging_data = validated_data.pop("packaging", None)
        category_data = validated_data.pop("category")
        subcategories_data = validated_data.pop("subcategories", [])

        # Handle category
        category, _ = Category.objects.get_or_create(name=category_data["name"])

        # Handle subcategories
        subcategory_objs = [
            SubCategory.objects.get_or_create(name=data["name"])[0]
            for data in subcategories_data
        ]

        # Handle packaging
        packaging = None
        if packaging_data:
            packaging, _ = Packaging.objects.get_or_create(
                packaging_quantity=packaging_data["packaging_quantity"],
                packaging_value=packaging_data["packaging_value"],
                packaging_type=packaging_data["packaging_type"],
            )

        # Create product
        product = Product.objects.create(
            category=category, packaging=packaging, **validated_data
        )
        product.subcategories.set(subcategory_objs)

        return product

    def update(self, instance, validated_data):
        """
        Update an existing product with nested relationships.
        """
        packaging_data = validated_data.pop("packaging", None)
        category_data = validated_data.pop("category", None)
        subcategories_data = validated_data.pop("subcategories", [])

        # Handle packaging
        if packaging_data:
            packaging, _ = Packaging.objects.get_or_create(
                packaging_quantity=packaging_data["packaging_quantity"],
                packaging_value=packaging_data["packaging_value"],
                packaging_type=packaging_data["packaging_type"],
            )
            instance.packaging = packaging

        # Handle category
        if category_data:
            category, _ = Category.objects.get_or_create(name=category_data["name"])
            instance.category = category

        # Handle subcategories
        if subcategories_data:
            subcategory_objs = [
                SubCategory.objects.get_or_create(name=data["name"])[0]
                for data in subcategories_data
            ]
            instance.subcategories.set(subcategory_objs)

        # Update fields
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class StockSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)
    product_name = serializers.CharField(source="product.product_name", read_only=True)

    class Meta:
        model = Stock
        fields = [
            "store_id",
            "store_name",
            "product",
            "product_name",
            "quantity_in_stock",
            "expiration_date",
        ]

    def create(self, validated_data):
        """Create a new Stock instance."""
        return Stock.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing Stock instance."""
        instance.store = validated_data.get("store", instance.store)
        instance.product = validated_data.get("product", instance.product)
        instance.quantity_in_stock = validated_data.get(
            "quantity_in_stock", instance.quantity_in_stock
        )
        instance.expiration_date = validated_data.get(
            "expiration_date", instance.expiration_date
        )
        instance.save()
        return instance

    def validate(self, attrs):
        """
        Perform custom validation for the Stock model.
        Ensures the expiration date is in the future and checks for duplicate stock entries.
        """
        expiration_date = attrs.get("expiration_date")
        if expiration_date and expiration_date < datetime.date.today():
            raise serializers.ValidationError(
                {"expiration_date": "Expiration date must be in the future."}
            )

        store = attrs.get("store")
        product = attrs.get("product")
        if Stock.objects.filter(store=store, product=product).exists():
            raise serializers.ValidationError(
                "A stock entry for this store and product already exists."
            )

        return attrs

    def validate_quantity_in_stock(self, value):
        """Ensure quantity in stock is not negative."""
        if value < 0:
            raise serializers.ValidationError("Quantity in stock cannot be negative.")
        return value
