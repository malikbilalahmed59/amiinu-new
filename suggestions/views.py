import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import uuid
import httpx
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Country, ShippingService, ShippingRoute
from .serializers import CountrySerializer, ShippingServiceSerializer, ShippingRouteSerializer


class CountryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing countries with full CRUD operations
    """
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]


class ShippingServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shipping services with full CRUD operations
    """
    queryset = ShippingService.objects.all().order_by('service_type')
    serializer_class = ShippingServiceSerializer
    permission_classes = [IsAuthenticated]


class ControlRateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shipping routes with full CRUD operations
    """
    queryset = ShippingRoute.objects.all().select_related(
        'shipping_from', 'shipping_to', 'service'
    )
    serializer_class = ShippingRouteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['shipping_from', 'shipping_to', 'service', 'is_active']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by weight range
        weight = self.request.query_params.get('weight', None)
        if weight:
            try:
                weight_val = float(weight)
                queryset = queryset.filter(
                    min_weight__lte=weight_val,
                    weight_limit__gte=weight_val
                )
            except ValueError:
                pass

        return queryset.order_by('shipping_from__name', 'shipping_to__name')


from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import requests
from django.conf import settings


@api_view(['POST'])
def calculate_shipping_rates(request):
    """Calculate shipping rates for all available services based on pickup/delivery addresses."""

    # Extract data from request
    pickup_address = request.data.get('pickup_address', {})
    delivery_address = request.data.get('delivery_address', {})
    pickup_date = request.data.get('pickup_date')
    containers = request.data.get('containers', [])

    # Validate required fields
    if not all([pickup_address, delivery_address, pickup_date, containers]):
        return Response(
            {"error": "Missing required fields: pickup_address, delivery_address, pickup_date, containers"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Extract coordinates
    pickup_lat = pickup_address.get('latitude')
    pickup_lng = pickup_address.get('longitude')
    delivery_lat = delivery_address.get('latitude')
    delivery_lng = delivery_address.get('longitude')

    if not all([pickup_lat, pickup_lng, delivery_lat, delivery_lng]):
        return Response(
            {"error": "Missing coordinates in pickup or delivery address"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get countries from coordinates using Google Geocoding API
        pickup_country = get_country_from_coordinates(pickup_lat, pickup_lng)
        delivery_country = get_country_from_coordinates(delivery_lat, delivery_lng)

        if not pickup_country or not delivery_country:
            return Response(
                {"error": "Could not determine countries from coordinates"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find countries in database
        from_country = Country.objects.filter(name__iexact=pickup_country).first()
        to_country = Country.objects.filter(name__iexact=delivery_country).first()

        if not from_country:
            # Try to find partial matches
            from_country = Country.objects.filter(name__icontains=pickup_country).first()

        if not to_country:
            # Try to find partial matches
            to_country = Country.objects.filter(name__icontains=delivery_country).first()

        if not from_country or not to_country:
            return Response({
                "error": f"Countries not found in database. Pickup: {pickup_country}, Delivery: {delivery_country}",
                "available_countries": list(Country.objects.values_list('name', flat=True))[:10] + ["..."]
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate total weight and dimensions
        total_weight = Decimal('0')
        total_volume = Decimal('0')

        for container in containers:
            weight = Decimal(str(container.get('weight', 0)))
            quantity = int(container.get('quantity', 1))
            length = Decimal(str(container.get('length', 0)))
            width = Decimal(str(container.get('width', 0)))
            height = Decimal(str(container.get('height', 0)))

            total_weight += weight * quantity
            total_volume += (length * width * height * quantity) / 1000000  # Convert to cubic meters

        # Get all routes between the countries
        routes = ShippingRoute.objects.filter(
            shipping_from=from_country,
            shipping_to=to_country,
            is_active=True
        ).select_related('service')

        if not routes.exists():
            return Response({
                "error": f"No shipping routes available from {from_country.name} to {to_country.name}"
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate rates for each service
        shipping_options = []

        for route in routes:
            service_type = route.service.service_type

            # Check weight compatibility
            weight_diff = abs(total_weight - route.weight_limit)

            # Apply business rules for weight differences
            if service_type in ['economy_air', 'express_air', 'connect_plus']:
                if weight_diff > 10:
                    continue  # Skip this service as it's unavailable
            elif service_type in ['fcl_sea', 'lcl_sea']:
                if weight_diff > 50:
                    continue  # Skip this service as it's unavailable

            # Check if weight is within min and max limits
            if total_weight < route.min_weight or total_weight > route.weight_limit:
                # Find the closest weight range route for this service
                closest_route = find_closest_weight_route(
                    from_country, to_country, route.service, total_weight
                )
                if closest_route:
                    route = closest_route
                else:
                    continue  # No suitable route found

            # Calculate final price with profit margin
            base_price = route.price
            profit_amount = (base_price * route.profit_margin) / 100
            final_price = base_price + profit_amount

            shipping_option = {
                "service_type": service_type,
                "service_name": route.service.get_service_type_display(),
                "rate_name": route.rate_name,
                "transit_time": route.transit_time,
                "base_price": float(base_price),
                "profit_margin": float(route.profit_margin),
                "final_price": float(final_price),
                "weight_limit": float(route.weight_limit),
                "min_weight": float(route.min_weight),
                "total_weight": float(total_weight),
                "currency": "USD",  # Assuming USD, adjust as needed
                "route_id": route.id,  # IMPORTANT: Include route ID for profit tracking
                # Additional info for frontend
                "origin_country_id": from_country.id,
                "destination_country_id": to_country.id,
                "profit_amount": float(profit_amount)  # Show profit amount to frontend if needed
            }

            shipping_options.append(shipping_option)

        # Sort by final price
        shipping_options.sort(key=lambda x: x['final_price'])

        response_data = {
            "pickup_country": from_country.name,
            "pickup_country_id": from_country.id,  # Include country IDs
            "delivery_country": to_country.name,
            "delivery_country_id": to_country.id,
            "pickup_date": pickup_date,
            "total_weight_kg": float(total_weight),
            "total_volume_m3": float(total_volume),
            "shipping_options": shipping_options,
            "container_count": len(containers)
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_country_from_coordinates(lat, lng):
    """Get country name from coordinates using Google Geocoding API."""
    api_key = settings.GOOGLE_PLACES_API_KEY
    url = f"https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "latlng": f"{lat},{lng}",
        "key": api_key,
        "result_type": "country"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            # Extract country from the first result
            for result in data["results"]:
                for component in result.get("address_components", []):
                    if "country" in component.get("types", []):
                        return component.get("long_name")

        # If no country result, try without result_type filter
        params.pop("result_type")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            for result in data["results"]:
                for component in result.get("address_components", []):
                    if "country" in component.get("types", []):
                        return component.get("long_name")

        return None

    except Exception as e:
        print(f"Error getting country from coordinates: {str(e)}")
        return None


def find_closest_weight_route(from_country, to_country, service, target_weight):
    """Find the route with the closest weight limit for the given service."""
    routes = ShippingRoute.objects.filter(
        shipping_from=from_country,
        shipping_to=to_country,
        service=service,
        is_active=True
    ).order_by('weight_limit')

    if not routes.exists():
        return None

    # Find route where target_weight fits between min_weight and weight_limit
    for route in routes:
        if route.min_weight <= target_weight <= route.weight_limit:
            return route

    # If no exact fit, find the closest one
    closest_route = None
    min_diff = float('inf')

    for route in routes:
        # Check if weight is above the route's capacity
        if target_weight > route.weight_limit:
            diff = target_weight - route.weight_limit
        else:
            # Weight is below minimum
            diff = route.min_weight - target_weight

        if diff < min_diff:
            min_diff = diff
            closest_route = route

    return closest_route









# Use persistent connection pooling for speed
client = httpx.Client(
    timeout=5.0,  # Fast timeout
    headers={"Accept-Encoding": "gzip, deflate"},  # Request compressed responses
)


@api_view(['GET'])
def address_suggestions(request):
    """Fetch optimized address suggestions from Google Places API with coordinates."""

    query = request.GET.get('query', '').strip()
    if not query:
        return Response(
            {"error": "Query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    session_token = request.GET.get('sessiontoken', str(uuid.uuid4()))
    api_key = settings.GOOGLE_PLACES_API_KEY
    autocomplete_endpoint = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "input": query,
        "key": api_key,
        "types": "geocode",
        "language": "en",
        "sessiontoken": session_token
    }

    try:
        # Make the request to Autocomplete API
        response = client.get(autocomplete_endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        # Handle Google API response status
        google_status = data.get("status", "")

        if google_status == "OK":
            suggestions = []

            for place in data.get("predictions", []):
                place_id = place["place_id"]

                # Request place details to get coordinates
                details_params = {
                    "place_id": place_id,
                    "fields": "geometry",
                    "key": api_key,
                    "sessiontoken": session_token  # Reuse the same session token
                }

                details_response = client.get(details_endpoint, params=details_params)
                details_response.raise_for_status()
                details_data = details_response.json()

                # Extract coordinates if available
                location = None
                if details_data.get("status") == "OK":
                    geometry = details_data.get("result", {}).get("geometry", {})
                    location = geometry.get("location", {})

                suggestions.append({
                    "description": place["description"],
                    "place_id": place_id,
                    "location": {
                        "lat": location.get("lat") if location else None,
                        "lng": location.get("lng") if location else None
                    }
                })

            return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)

        elif google_status == "ZERO_RESULTS":
            return Response(
                {"error": "No results found for the given query."},
                status=status.HTTP_404_NOT_FOUND
            )

        elif google_status == "OVER_QUERY_LIMIT":
            return Response(
                {"error": "Google API quota exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        elif google_status == "REQUEST_DENIED":
            return Response(
                {"error": "Google API request denied. Check API key & billing."},
                status=status.HTTP_403_FORBIDDEN
            )

        elif google_status == "INVALID_REQUEST":
            return Response(
                {"error": "Invalid request. Missing or incorrect parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        else:
            return Response(
                {"error": f"Unexpected Google API error: {google_status}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except httpx.RequestError as e:
        return Response(
            {"error": f"Failed to connect to Google API: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except Exception as e:
        return Response(
            {"error": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


