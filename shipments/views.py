from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Shipment
from .serializers import ShipmentSerializer
# analytics_views.py for shipment app

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from .models import Shipment
from suggestions.models import Country


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_analytics(request):
    """
    Get comprehensive dashboard analytics including profits, order counts, and trends.

    Query params:
    - origin_country: Filter by origin country ID
    - destination_country: Filter by destination country ID
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    """
    user = request.user

    # Get query parameters
    origin_country_id = request.GET.get('origin_country')
    destination_country_id = request.GET.get('destination_country')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Base queryset - only paid shipments for profit calculations
    base_queryset = Shipment.objects.filter(user=user, payment_status='paid')

    # Apply filters
    if origin_country_id:
        base_queryset = base_queryset.filter(origin_country_id=origin_country_id)

    if destination_country_id:
        base_queryset = base_queryset.filter(destination_country_id=destination_country_id)

    if start_date:
        base_queryset = base_queryset.filter(created_at__date__gte=start_date)

    if end_date:
        base_queryset = base_queryset.filter(created_at__date__lte=end_date)

    # Calculate date ranges
    today = datetime.now().date()
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    year_ago = today - timedelta(days=365)

    # Overall statistics
    overall_stats = base_queryset.aggregate(
        total_revenue=Sum('delivery_price'),
        total_cost=Sum('base_cost'),
        total_profit=Sum('profit_amount'),
        total_orders=Count('id'),
        avg_profit_margin=Sum(F('profit_margin_percentage')) / Count('id')
    )

    # Time-based statistics
    current_month_stats = base_queryset.filter(created_at__date__gte=month_ago).aggregate(
        revenue=Sum('delivery_price'),
        profit=Sum('profit_amount'),
        orders=Count('id')
    )

    three_month_stats = base_queryset.filter(created_at__date__gte=three_months_ago).aggregate(
        revenue=Sum('delivery_price'),
        profit=Sum('profit_amount'),
        orders=Count('id')
    )

    yearly_stats = base_queryset.filter(created_at__date__gte=year_ago).aggregate(
        revenue=Sum('delivery_price'),
        profit=Sum('profit_amount'),
        orders=Count('id')
    )

    # Monthly trends (last 12 months)
    monthly_trends = base_queryset.filter(
        created_at__date__gte=year_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('delivery_price'),
        profit=Sum('profit_amount'),
        orders=Count('id')
    ).order_by('month')

    # Top profitable routes
    top_routes = base_queryset.values(
        'origin_country__name',
        'destination_country__name',
        'shipping_route__service__service_type'
    ).annotate(
        total_profit=Sum('profit_amount'),
        order_count=Count('id'),
        avg_profit=Sum('profit_amount') / Count('id')
    ).order_by('-total_profit')[:10]

    # Profit by country (origin)
    profit_by_origin = base_queryset.values(
        'origin_country__name'
    ).annotate(
        total_profit=Sum('profit_amount'),
        order_count=Count('id'),
        total_revenue=Sum('delivery_price')
    ).order_by('-total_profit')

    # Profit by service type
    profit_by_service = base_queryset.values(
        'international_shipping_type'
    ).annotate(
        total_profit=Sum('profit_amount'),
        order_count=Count('id'),
        avg_profit_margin=Sum(F('profit_margin_percentage')) / Count('id')
    ).order_by('-total_profit')

    # Status distribution (all shipments, not just paid)
    all_shipments = Shipment.objects.filter(user=user)
    if origin_country_id:
        all_shipments = all_shipments.filter(origin_country_id=origin_country_id)
    if destination_country_id:
        all_shipments = all_shipments.filter(destination_country_id=destination_country_id)

    status_distribution = all_shipments.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    response_data = {
        'overall_statistics': {
            'total_revenue': float(overall_stats['total_revenue'] or 0),
            'total_cost': float(overall_stats['total_cost'] or 0),
            'total_profit': float(overall_stats['total_profit'] or 0),
            'total_orders': overall_stats['total_orders'],
            'average_profit_margin': float(overall_stats['avg_profit_margin'] or 0),
        },
        'time_based_statistics': {
            'current_month': {
                'revenue': float(current_month_stats['revenue'] or 0),
                'profit': float(current_month_stats['profit'] or 0),
                'orders': current_month_stats['orders']
            },
            'three_months': {
                'revenue': float(three_month_stats['revenue'] or 0),
                'profit': float(three_month_stats['profit'] or 0),
                'orders': three_month_stats['orders']
            },
            'yearly': {
                'revenue': float(yearly_stats['revenue'] or 0),
                'profit': float(yearly_stats['profit'] or 0),
                'orders': yearly_stats['orders']
            }
        },
        'monthly_trends': [
            {
                'month': trend['month'].strftime('%Y-%m'),
                'revenue': float(trend['revenue'] or 0),
                'profit': float(trend['profit'] or 0),
                'orders': trend['orders']
            }
            for trend in monthly_trends
        ],
        'top_profitable_routes': [
            {
                'origin': route['origin_country__name'],
                'destination': route['destination_country__name'],
                'service_type': route['shipping_route__service__service_type'],
                'total_profit': float(route['total_profit'] or 0),
                'order_count': route['order_count'],
                'average_profit': float(route['avg_profit'] or 0)
            }
            for route in top_routes
        ],
        'profit_by_origin_country': [
            {
                'country': country['origin_country__name'],
                'total_profit': float(country['total_profit'] or 0),
                'order_count': country['order_count'],
                'total_revenue': float(country['total_revenue'] or 0)
            }
            for country in profit_by_origin
        ],
        'profit_by_service_type': [
            {
                'service_type': service['international_shipping_type'],
                'total_profit': float(service['total_profit'] or 0),
                'order_count': service['order_count'],
                'average_profit_margin': float(service['avg_profit_margin'] or 0)
            }
            for service in profit_by_service
        ],
        'status_distribution': [
            {
                'status': status['status'],
                'count': status['count']
            }
            for status in status_distribution
        ],
        'filters_applied': {
            'origin_country_id': origin_country_id,
            'destination_country_id': destination_country_id,
            'start_date': start_date,
            'end_date': end_date
        }
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profit_report(request):
    """
    Get detailed profit report with filtering options.

    Query params:
    - group_by: 'country', 'route', 'service', 'month' (default: 'country')
    - origin_country: Filter by origin country ID
    - start_date: Start date for filtering
    - end_date: End date for filtering
    """
    user = request.user
    group_by = request.GET.get('group_by', 'country')
    origin_country_id = request.GET.get('origin_country')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Base queryset
    queryset = Shipment.objects.filter(user=user, payment_status='paid')

    # Apply filters
    if origin_country_id:
        queryset = queryset.filter(origin_country_id=origin_country_id)

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    if group_by == 'country':
        report_data = queryset.values(
            'origin_country__name',
            'origin_country__id'
        ).annotate(
            total_revenue=Sum('delivery_price'),
            total_cost=Sum('base_cost'),
            total_profit=Sum('profit_amount'),
            order_count=Count('id'),
            avg_profit_margin=Sum(F('profit_margin_percentage')) / Count('id')
        ).order_by('-total_profit')

    elif group_by == 'route':
        report_data = queryset.values(
            'origin_country__name',
            'destination_country__name',
            'shipping_route__id'
        ).annotate(
            total_revenue=Sum('delivery_price'),
            total_cost=Sum('base_cost'),
            total_profit=Sum('profit_amount'),
            order_count=Count('id'),
            avg_profit_margin=Sum(F('profit_margin_percentage')) / Count('id')
        ).order_by('-total_profit')

    elif group_by == 'service':
        report_data = queryset.values(
            'international_shipping_type'
        ).annotate(
            total_revenue=Sum('delivery_price'),
            total_cost=Sum('base_cost'),
            total_profit=Sum('profit_amount'),
            order_count=Count('id'),
            avg_profit_margin=Sum(F('profit_margin_percentage')) / Count('id')
        ).order_by('-total_profit')

    elif group_by == 'month':
        report_data = queryset.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_revenue=Sum('delivery_price'),
            total_cost=Sum('base_cost'),
            total_profit=Sum('profit_amount'),
            order_count=Count('id'),
            avg_profit_margin=Sum(F('profit_margin_percentage')) / Count('id')
        ).order_by('-month')

    else:
        return Response(
            {"error": "Invalid group_by parameter. Use 'country', 'route', 'service', or 'month'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Format the response
    formatted_data = []
    for item in report_data:
        formatted_item = {
            'total_revenue': float(item['total_revenue'] or 0),
            'total_cost': float(item['total_cost'] or 0),
            'total_profit': float(item['total_profit'] or 0),
            'order_count': item['order_count'],
            'average_profit_margin': float(item['avg_profit_margin'] or 0)
        }

        if group_by == 'country':
            formatted_item['country'] = item['origin_country__name']
            formatted_item['country_id'] = item['origin_country__id']
        elif group_by == 'route':
            formatted_item['origin'] = item['origin_country__name']
            formatted_item['destination'] = item['destination_country__name']
            formatted_item['route_id'] = item['shipping_route__id']
        elif group_by == 'service':
            formatted_item['service_type'] = item['international_shipping_type']
        elif group_by == 'month':
            formatted_item['month'] = item['month'].strftime('%Y-%m')

        formatted_data.append(formatted_item)

    response_data = {
        'group_by': group_by,
        'filters': {
            'origin_country_id': origin_country_id,
            'start_date': start_date,
            'end_date': end_date
        },
        'data': formatted_data,
        'summary': {
            'total_profit': sum(item['total_profit'] for item in formatted_data),
            'total_revenue': sum(item['total_revenue'] for item in formatted_data),
            'total_orders': sum(item['order_count'] for item in formatted_data)
        }
    }

    return Response(response_data, status=status.HTTP_200_OK)

class ShipmentViewSet(ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Validation Errors:", serializer.errors)  # Debugging validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            print("Validation Errors:", serializer.errors)  # Debugging validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)
