# admin.py
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import HttpResponse
from django import forms
import csv
from .models import Country, ShippingService, ShippingRoute


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File",
        help_text="CSV format: shipping_from,shipping_to,service_type,rate_name,weight_limit,transit_time,price,profit_margin,min_weight"
    )


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(ShippingService)
class ShippingServiceAdmin(admin.ModelAdmin):
    list_display = ['get_service_type_display', 'service_type']
    list_filter = ['service_type']
    ordering = ['service_type']

    def get_service_type_display(self, obj):
        return obj.get_service_type_display()

    get_service_type_display.short_description = 'Service Type'


@admin.register(ShippingRoute)
class ShippingRouteAdmin(admin.ModelAdmin):
    list_display = [
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
        'is_active'
    ]
    search_fields = [
        'shipping_from__name',
        'shipping_to__name',
        'service__service_type',
        'rate_name'
    ]
    ordering = ['shipping_from', 'shipping_to', 'service']

    fieldsets = (
        ('Route Information', {
            'fields': ('shipping_from', 'shipping_to', 'service')
        }),
        ('Pricing Details', {
            'fields': (
                'rate_name',
                ('min_weight', 'weight_limit'),
                'price',
                'profit_margin'
            )
        }),
        ('Service Details', {
            'fields': ('transit_time', 'is_active')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'upload-csv/',
                self.admin_site.admin_view(self.upload_csv),
                name='shippingroute_upload_csv'
            ),
            path(
                'download-template/',
                self.admin_site.admin_view(self.download_template),
                name='shippingroute_download_template'
            ),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']

                # Validate file extension
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'Please upload a CSV file.')
                    return render(request, 'admin/upload_csv.html', {'form': form})

                # Process CSV
                results = ShippingRoute.create_or_update_from_csv(csv_file)

                # Display results
                if results['errors']:
                    for error in results['errors']:
                        messages.error(request, error)

                success_msg = f"CSV processed successfully! Created: {results['created']}, Updated: {results['updated']}"
                if results['errors']:
                    success_msg += f", Errors: {len(results['errors'])}"

                messages.success(request, success_msg)
                return redirect('..')
        else:
            form = CSVUploadForm()

        return render(request, 'admin/upload_csv.html', {
            'form': form,
            'title': 'Upload Shipping Routes CSV',
            'opts': self.model._meta,
        })

    def download_template(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shipping_routes_template.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'shipping_from',
            'shipping_to',
            'service_type',
            'rate_name',
            'weight_limit',
            'transit_time',
            'price',
            'profit_margin',
            'min_weight'
        ])

        # Add sample data
        writer.writerow([
            'Canada',
            'USA',
            'economy_air',
            'Standard Rate',
            'flat_rate',
            '50',
            '4 days',
            '70',
            '40',
            '0'
        ])

        return response

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_buttons'] = [
            {
                'url': 'upload-csv/',
                'title': 'Upload CSV',
                'class': 'addlink'
            },
            {
                'url': 'download-template/',
                'title': 'Download Template',
                'class': 'addlink'
            }
        ]
        return super().changelist_view(request, extra_context=extra_context)