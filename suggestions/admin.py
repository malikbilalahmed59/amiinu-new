# admin.py
from django.contrib import admin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from .models import Country, ShippingService, ShippingRoute


class CountryResource(resources.ModelResource):
    class Meta:
        model = Country
        fields = ('id', 'name')
        export_order = ('id', 'name')


class ShippingServiceResource(resources.ModelResource):
    service_type_display = fields.Field(
        column_name='service_type_display',
        attribute='get_service_type_display',
        readonly=True
    )

    class Meta:
        model = ShippingService
        fields = ('id', 'service_type', 'service_type_display')
        export_order = ('id', 'service_type', 'service_type_display')



class ShippingRouteResource(resources.ModelResource):
    # Simple field definitions for export
    shipping_from_name = fields.Field(
        column_name='shipping_from_name',
        attribute='shipping_from__name',
        readonly=True
    )

    shipping_to_name = fields.Field(
        column_name='shipping_to_name',
        attribute='shipping_to__name',
        readonly=True
    )

    service_type = fields.Field(
        column_name='service_type',
        attribute='service__service_type',
        readonly=True
    )

    service_display = fields.Field(
        column_name='service_display',
        attribute='service__get_service_type_display',
        readonly=True
    )

    class Meta:
        model = ShippingRoute
        fields = (
            'id', 'rate_name', 'shipping_from_name', 'shipping_to_name',
            'service_type', 'service_display', 'weight_limit', 'min_weight',
            'transit_time', 'price', 'profit_margin', 'is_active',
            'created_at', 'updated_at'
        )
        export_order = (
            'id', 'rate_name', 'shipping_from_name', 'shipping_to_name',
            'service_type', 'weight_limit', 'min_weight',
            'price', 'profit_margin', 'transit_time', 'is_active'
        )
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):

        from_country_name = row.get('shipping_from_name')
        if from_country_name:
            from_country, created = Country.objects.get_or_create(name=from_country_name)
            row['shipping_from'] = from_country.id
            row['_from_country_obj'] = from_country

        # Handle shipping_to
        to_country_name = row.get('shipping_to_name')
        if to_country_name:
            to_country, created = Country.objects.get_or_create(name=to_country_name)
            row['shipping_to'] = to_country.id
            # Store for duplicate checking
            row['_to_country_obj'] = to_country

        # Handle service - try multiple column names and formats
        service_value = (
                row.get('service_type') or
                row.get('service') or
                row.get('service_display', '')
        )

        if service_value:
            # Clean and map service types
            service_mapping = {
                # From display names
                'express air': 'express_air',
                'economy air': 'economy_air',
                'fcl (full container load) sea': 'fcl_sea',
                'lcl (less than container load) sea': 'lcl_sea',
                'connect plus': 'connect_plus',
                # From service types (already correct)
                'express_air': 'express_air',
                'economy_air': 'economy_air',
                'fcl_sea': 'fcl_sea',
                'lcl_sea': 'lcl_sea',
                'connect_plus': 'connect_plus',
                # Handle other variations
                'fcl sea': 'fcl_sea',
                'lcl sea': 'lcl_sea',
            }

            service_type_clean = service_value.lower().strip()
            correct_service_type = service_mapping.get(service_type_clean, service_type_clean)

            service, created = ShippingService.objects.get_or_create(
                service_type=correct_service_type
            )
            row['service'] = service.id
            row['_service_obj'] = service

    def get_instance(self, instance_loader, row):

        from_country = row.get('_from_country_obj')
        to_country = row.get('_to_country_obj')
        service = row.get('_service_obj')

        rate_name = row.get('rate_name')
        weight_limit = row.get('weight_limit')
        min_weight = row.get('min_weight')

        if from_country and to_country and service and rate_name and weight_limit and min_weight:
            try:
                weight_limit_decimal = float(weight_limit)
                min_weight_decimal = float(min_weight)

                existing_route = ShippingRoute.objects.get(
                    shipping_from=from_country,
                    shipping_to=to_country,
                    service=service,
                    rate_name=rate_name,
                    weight_limit=weight_limit_decimal,
                    min_weight=min_weight_decimal
                )
                print(
                    f"Found EXACT match: {existing_route.rate_name} ({from_country.name} -> {to_country.name}) - Will UPDATE")
                return existing_route

            except ShippingRoute.DoesNotExist:
                # Check if similar route exists (for info only)
                similar_routes = ShippingRoute.objects.filter(
                    shipping_from=from_country,
                    shipping_to=to_country,
                    service=service
                ).count()

                if similar_routes > 0:
                    print(
                        f"Found {similar_routes} similar route(s) for {from_country.name} -> {to_country.name} via {service.service_type}, but different weight/name - Will CREATE NEW")
                else:
                    print(
                        f"No existing routes found for {from_country.name} -> {to_country.name} via {service.service_type} - Will CREATE NEW")

        return None

    def import_obj(self, obj, data, dry_run, **kwargs):

        if 'shipping_from' in data:
            obj.shipping_from_id = data['shipping_from']
        if 'shipping_to' in data:
            obj.shipping_to_id = data['shipping_to']
        if 'service' in data:
            obj.service_id = data['service']


        for field in ['rate_name', 'weight_limit', 'min_weight', 'transit_time',
                      'price', 'profit_margin', 'is_active']:
            if field in data:
                setattr(obj, field, data[field])

        return obj

    def skip_row(self, instance, original, row, import_validation_errors=None):

        if import_validation_errors:
            return True

        if instance and hasattr(instance, 'pk') and instance.pk:
            return False



        # If no exact match, will create new record
        return False

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
    resource_class = CountryResource
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

    # Import/Export settings
    list_per_page = 50
    list_max_show_all = 200


@admin.register(ShippingService)
class ShippingServiceAdmin(ImportExportModelAdmin):
    resource_class = ShippingServiceResource
    list_display = ['get_service_type_display', 'service_type']
    list_filter = ['service_type']
    ordering = ['service_type']

    def get_service_type_display(self, obj):
        return obj.get_service_type_display()

    get_service_type_display.short_description = 'Service Type'


@admin.register(ShippingRoute)
class ShippingRouteAdmin(ImportExportModelAdmin):
    resource_class = ShippingRouteResource

    list_display = [
        'rate_name',
        'shipping_from',
        'shipping_to',
        'service',
        'weight_limit',
        'price',
        'profit_margin',
        'transit_time',
        'is_active'
    ]

    list_filter = [
        'shipping_from',
        'shipping_to',
        'service__service_type',
        'is_active',
        'created_at'
    ]

    search_fields = [
        'shipping_from__name',
        'shipping_to__name',
        'service__service_type',
        'rate_name'
    ]

    list_editable = ['price', 'profit_margin', 'is_active']

    # Import/Export settings
    list_per_page = 25
    date_hierarchy = 'created_at'

    # Fieldsets for better organization
    fieldsets = (
        ('Route Information', {
            'fields': ('rate_name', 'shipping_from', 'shipping_to', 'service')
        }),
        ('Pricing & Limits', {
            'fields': ('price', 'profit_margin', 'weight_limit', 'min_weight')
        }),
        ('Service Details', {
            'fields': ('transit_time', 'is_active')
        }),
    )

    # Custom actions
    actions = ['activate_routes', 'deactivate_routes', 'duplicate_routes']

    def activate_routes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} routes were activated.')

    activate_routes.short_description = "Activate selected routes"

    def deactivate_routes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} routes were deactivated.')

    deactivate_routes.short_description = "Deactivate selected routes"

    def duplicate_routes(self, request, queryset):
        """Duplicate selected routes with modified names"""
        count = 0
        for route in queryset:
            route.pk = None  # This will create a new object
            route.rate_name = f"{route.rate_name} (Copy)"
            route.save()
            count += 1
        self.message_user(request, f'{count} routes were duplicated.')

    duplicate_routes.short_description = "Duplicate selected routes"