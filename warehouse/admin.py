from django.contrib import admin
from .models import (
    Warehouse,
    InboundShipment,
    Product,
    Variation,
    VariationOption,
    OutboundShipment,
    OutboundShipmentItem
)

# Variation Option Inline for Variation
class VariationOptionInline(admin.TabularInline):
    model = VariationOption
    extra = 1
    fields = ['name', 'quantity']

# Variation Inline for Product
class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1
    fields = ['type']

# Product Inline for InboundShipment
class ProductInline(admin.TabularInline):
    model = Product
    extra = 1
    fields = ['name', 'sku', 'weight', 'dimensions']

# OutboundShipmentItem Inline for OutboundShipment
class OutboundShipmentItemInline(admin.TabularInline):
    model = OutboundShipmentItem
    extra = 1
    fields = ['product', 'variation_option', 'quantity']
    autocomplete_fields = ['product', 'variation_option']

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['country', 'created_at', 'updated_at']
    search_fields = ['country']

@admin.register(InboundShipment)
class InboundShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_number',
        'warehouse',
        'user',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'warehouse']
    search_fields = ['tracking_number', 'user__username']
    readonly_fields = [
        'pending_at',
        'in_transit_at',
        'received_at',
        'completed_at',
        'cancelled_at',
        'created_at',
        'updated_at'
    ]
    fieldsets = [
        ('Basic Information', {
            'fields': ['warehouse', 'user', 'tracking_number', 'shipment_method', 'status']
        }),
        ('Timestamps', {
            'fields': [
                'pending_at',
                'in_transit_at',
                'received_at',
                'completed_at',
                'cancelled_at',
                'created_at',
                'updated_at'
            ],
            'classes': ['collapse']
        })
    ]
    inlines = [ProductInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'warehouse', 'inbound_shipments']
    list_filter = ['warehouse']
    search_fields = ['name', 'sku']
    inlines = [VariationInline]

@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ['type', 'product']
    list_filter = ['type']
    search_fields = ['type', 'product__name']
    autocomplete_fields = ['product']
    inlines = [VariationOptionInline]

@admin.register(VariationOption)
class VariationOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'variation', 'quantity']
    list_filter = ['variation__type']
    search_fields = ['name', 'variation__type', 'variation__product__name']
    autocomplete_fields = ['variation']

@admin.register(OutboundShipment)
class OutboundShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_number',
        'customer_name',
        'warehouse',
        'status',
        'estimated_delivery',
        'created_at'
    ]
    list_filter = ['status', 'warehouse']
    search_fields = ['tracking_number', 'customer_name', 'user__username']
    readonly_fields = [
        'pending_at',
        'shipped_at',
        'delivered_at',
        'cancelled_at',
        'created_at',
        'updated_at'
    ]
    fieldsets = [
        ('Customer Information', {
            'fields': ['customer_name', 'customer_address']
        }),
        ('Shipment Details', {
            'fields': [
                'warehouse',
                'user',
                'tracking_number',
                'shipment_method',
                'status',
                'estimated_delivery'
            ]
        }),
        ('Timestamps', {
            'fields': [
                'pending_at',
                'shipped_at',
                'delivered_at',
                'cancelled_at',
                'created_at',
                'updated_at'
            ],
            'classes': ['collapse']
        })
    ]
    inlines = [OutboundShipmentItemInline]

@admin.register(OutboundShipmentItem)
class OutboundShipmentItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'variation_option', 'quantity', 'outbound_shipment']
    list_filter = ['outbound_shipment__status']
    search_fields = ['product__name', 'outbound_shipment__tracking_number']
    autocomplete_fields = ['product', 'variation_option', 'outbound_shipment']