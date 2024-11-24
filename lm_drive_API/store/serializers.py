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
        fields = ["id", "name"]


class SubCategorySerializer(BaseCategorySerializer):
    class Meta:
        model = SubCategory
        fields = ["id", "name"]


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
        slug_field="name",  # This will display the brand's name instead of ID
    )
    category = CategorySerializer()
    subcategories = SubCategorySerializer(many=True)
    stock_summary = serializers.SerializerMethodField()
    packaging = PackagingSerializer()

    class Meta:
        model = Product
        fields = [
            "product_id",
            "product_name",
            "upc",
            "description",
            "price",
            "brand",
            "category",
            "subcategories",
            "image1",
            "image2",
            "image3",
            "packaging",
            "stock_summary",
        ]

    def get_stock_summary(self, obj):
        """Retrieve the stock summary for a product."""
        return obj.get_stock_summary()

    def to_representation(self, instance):
        """Customize representation for authenticated users."""
        representation = super().to_representation(instance)
        request = self.context.get("request")

        # Include stock summary and price for authenticated users only
        if request and request.user.is_authenticated:
            representation["stock_summary"] = self.get_stock_summary(instance)
            representation["price"] = instance.price
        else:
            representation.pop("stock_summary", None)
            representation.pop("price", None)

        # Add absolute URLs for images
        representation["image_urls"] = self.get_image_urls(instance)
        return representation

    def get_image_urls(self, obj):
        """Return the absolute URLs for all product images."""
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
        """Create a new product."""
        packaging_data = validated_data.pop("packaging", None)
        product_id = validated_data.get("product_id")
        upc = validated_data.get("upc")

        # Check for existing product
        if Product.objects.filter(product_id=product_id).exists():
            raise serializers.ValidationError(
                f"Product with product_id '{product_id}' already exists."
            )
        if Product.objects.filter(upc=upc).exists():
            raise serializers.ValidationError(
                f"Product with UPC '{upc}' already exists."
            )

        category_data = validated_data.pop("category")
        category, _ = Category.objects.get_or_create(name=category_data["name"])

        subcategories_data = validated_data.pop("subcategories", [])
        subcategory_objs = [
            SubCategory.objects.get_or_create(name=subcategory_data["name"])[0]
            for subcategory_data in subcategories_data
        ]

        packaging = None
        if packaging_data:
            packaging, _ = Packaging.objects.get_or_create(
                packaging_quantity=packaging_data.get("packaging_quantity"),
                packaging_value=packaging_data.get("packaging_value"),
                packaging_type=packaging_data.get("packaging_type"),
            )

        product = Product.objects.create(
            category=category, packaging=packaging, **validated_data
        )
        product.subcategories.set(subcategory_objs)
        return product

        """Update an existing product."""
        packaging_data = validated_data.pop("packaging", None)
        if packaging_data:
            packaging, _ = Packaging.objects.get_or_create(
                packaging_quantity=packaging_data["packaging_quantity"],
                packaging_value=packaging_data["packaging_value"],
                packaging_type=packaging_data["packaging_type"],
            )
            instance.packaging = packaging

        category_data = validated_data.pop("category", None)
        if category_data:
            category, _ = Category.objects.get_or_create(name=category_data["name"])
            instance.category = category

        subcategories_data = validated_data.pop("subcategories", [])
        if subcategories_data:
            subcategory_objs = [
                SubCategory.objects.get_or_create(name=subcategory_data["name"])[0]
                for subcategory_data in subcategories_data
            ]
            instance.subcategories.set(subcategory_objs)

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
