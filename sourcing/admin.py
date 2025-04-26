from django.contrib import admin
from .models import SourcingRequest, Quotation, Shipping


@admin.register(SourcingRequest)
class SourcingRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'status', 'quantity_needed', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'user__username', 'whatsapp_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('General Information', {
            'fields': ('user', 'name', 'description', 'quantity_needed', 'images')
        }),
        ('Contact Information', {
            'fields': ('whatsapp_number', 'address')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'sourcing_request', 'quotation_price', 'sent_at')
    list_filter = ('sent_at',)
    search_fields = ('sourcing_request__name', 'sourcing_request__user__username')
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at',)
    fieldsets = (
        ('Quotation Details', {
            'fields': ('sourcing_request', 'quotation_price', 'sent_at')
        }),
    )



@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ('id', 'sourcing_request', 'tracking_number', 'shipped_date', 'estimated_delivery_date')
    list_filter = ('shipped_date', 'estimated_delivery_date')
    search_fields = ('sourcing_request__name', 'sourcing_request__user__username', 'tracking_number')
    ordering = ('-shipped_date',)
    fieldsets = (
        ('Shipping Details', {
            'fields': ('sourcing_request', 'tracking_number', 'shipped_date', 'estimated_delivery_date', 'live_tracking_url')
        }),
    )
