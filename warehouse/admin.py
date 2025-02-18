from django.contrib import admin
from .models import Warehouse

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'created_at', 'updated_at')  # Columns to display
    search_fields = ('country',)  # Search by name & country
    list_filter = ('country',)  # Filter by country
    readonly_fields = ('created_at', 'updated_at')  # Make timestamps read-only
