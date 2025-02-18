from django.contrib import admin
from .models import Shipment, Container, Product

class ContainerInline(admin.TabularInline):
    model = Container
    extra = 1  # Number of empty forms to display
    show_change_link = True

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1
    show_change_link = True

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'shipment_type',
        'incoterm',
        'payment_status',
        'pickup_date',
        'created_at'
    )
    list_filter = ('shipment_type', 'payment_status', 'incoterm', 'created_at')
    search_fields = ('recipient_name', 'recipient_email', 'recipient_phone')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [ContainerInline]

@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipment', 'container_type', 'package_type', 'quantity', 'weight')
    list_filter = ('container_type', 'package_type')
    search_fields = ('shipment__id',)
    ordering = ('-id',)
    inlines = [ProductInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'container', 'name', 'hs_code')
    search_fields = ('name', 'hs_code')
    ordering = ('-id',)
