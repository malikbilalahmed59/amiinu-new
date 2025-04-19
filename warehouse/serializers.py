from rest_framework import serializers
from .models import Warehouse, Variation, Product, InboundShipment, VariationOption
from .models import OutboundShipment, OutboundShipmentItem


class VariationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariationOption
        fields = '__all__'


class VariationSerializer(serializers.ModelSerializer):
    options = VariationOptionSerializer(many=True)

    class Meta:
        model = Variation
        fields = ['id', 'product', 'type', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        variation = Variation.objects.create(**validated_data)

        for option_data in options_data:
            option_data.pop('variation', None)  # Remove if exists
            VariationOption.objects.create(variation=variation, **option_data)

        return variation


class ProductSerializer(serializers.ModelSerializer):
    variations = VariationSerializer(many=True, required=False)

    class Meta:
        model = Product
        exclude = ['warehouse', 'inbound_shipments']

    def create(self, validated_data):
        variations_data = validated_data.pop('variations', [])
        product = Product.objects.create(**validated_data)

        for variation_data in variations_data:
            variation_data.pop('product', None)  # Remove if exists

            VariationSerializer().create({**variation_data, 'product': product})

        return product


class InboundShipmentSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = InboundShipment
        fields = [
            'id', 'warehouse', 'user', 'tracking_number', 'shipment_method',
            'status', 'pending_at', 'in_transit_at', 'received_at',
            'completed_at', 'cancelled_at', 'created_at', 'updated_at',
            'products'
        ]
        read_only_fields = [
            'id', 'shipment_number', 'status', 'pending_at', 'in_transit_at', 'received_at',
            'completed_at', 'cancelled_at', 'created_at', 'updated_at'
        ]
        # Remove user from required fields - we'll set it in create
        extra_kwargs = {
            'user': {'required': False}
        }

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        warehouse = validated_data.get('warehouse')

        # Get the user from the request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        inbound_shipment = InboundShipment.objects.create(**validated_data)

        for product_data in products_data:
            product_data['inbound_shipments'] = inbound_shipment
            product_data['warehouse'] = warehouse
            ProductSerializer().create(product_data)

        return inbound_shipment

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if products_data is not None:
            # DELETE existing nested products and everything below
            instance.products.all().delete()

            warehouse = instance.warehouse
            for product_data in products_data:
                product_data['inbound_shipments'] = instance
                product_data['warehouse'] = warehouse
                ProductSerializer().create(product_data)

        return instance




class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'


from rest_framework import serializers
from django.db import transaction
from .models import OutboundShipment, OutboundShipmentItem  # Adjust imports as needed


class OutboundShipmentItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    variation_name = serializers.CharField(source='variation_option.name', read_only=True)

    class Meta:
        model = OutboundShipmentItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'variation_option', 'variation_name', 'quantity'
        ]

    def validate(self, data):
        variation_option = data.get('variation_option')
        quantity = data.get('quantity')

        if quantity is None or quantity <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")

        if variation_option:
            if variation_option.quantity is None:
                raise serializers.ValidationError(f"Variation option {variation_option.name} has no stock defined.")
            if variation_option.quantity < quantity:
                raise serializers.ValidationError(f"Not enough stock for {variation_option.name}")

        return data




class OutboundShipmentSerializer(serializers.ModelSerializer):
    items = OutboundShipmentItemSerializer(many=True)
    warehouse_country = serializers.CharField(source='warehouse.country', read_only=True)

    class Meta:
        model = OutboundShipment
        fields = [
            'id', 'warehouse', 'warehouse_country', 'user', 'customer_name',
            'customer_address', 'tracking_number', 'shipment_method',
            'status', 'pending_at', 'shipped_at', 'delivered_at',
            'cancelled_at', 'estimated_delivery', 'created_at', 'updated_at',
            'items'
        ]
        read_only_fields = [
            'id', 'shipment_number', 'status', 'pending_at', 'shipped_at',
            'delivered_at', 'cancelled_at', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'user': {'required': False}
        }

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        shipment = OutboundShipment.objects.create(**validated_data)

        for item_data in items_data:
            OutboundShipmentItem.objects.create(outbound_shipment=shipment, **item_data)

            variation_option = item_data.get('variation_option')
            if variation_option:
                variation_option.quantity -= item_data.get('quantity')
                variation_option.save()

        return shipment

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            existing_items = {item.variation_option_id: item for item in instance.items.all()}
            new_items_map = {item['variation_option'].id: item for item in items_data}

            # Removed items — restock and delete
            removed_ids = set(existing_items.keys()) - set(new_items_map.keys())
            for variation_id in removed_ids:
                item = existing_items[variation_id]
                variation = item.variation_option
                if variation:
                    variation.quantity += item.quantity
                    variation.save()
                item.delete()

            # Updated or new items
            for item_data in items_data:
                variation_option = item_data['variation_option']
                quantity = item_data['quantity']
                variation_id = variation_option.id

                if variation_id in existing_items:
                    existing_item = existing_items[variation_id]
                    delta = quantity - existing_item.quantity
                    if delta != 0:
                        variation_option.quantity -= delta
                        variation_option.save()
                        existing_item.quantity = quantity
                        existing_item.save()
                else:
                    OutboundShipmentItem.objects.create(outbound_shipment=instance, **item_data)
                    variation_option.quantity -= quantity
                    variation_option.save()

        return instance

    @transaction.atomic
    def delete(self, instance):
        """
        Custom delete logic to restore inventory before deleting the shipment.
        Note: This method must be called manually in the view — DRF serializers do not use delete().
        """
        for item in instance.items.all():
            variation_option = item.variation_option
            if variation_option:
                variation_option.quantity += item.quantity
                variation_option.save()
        instance.delete()

