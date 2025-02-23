import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
# from .models import APIUsage
import uuid
import httpx
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Use persistent connection pooling for speed
client = httpx.Client(
    timeout=5.0,  # Fast timeout
    headers={"Accept-Encoding": "gzip, deflate"},  # Request compressed responses
)

@api_view(['GET'])
def address_suggestions(request):
    """Fetch optimized address suggestions from Google Places API."""

    query = request.GET.get('query', '').strip()
    if not query:
        return Response(
            {"error": "Query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    session_token = request.GET.get('sessiontoken', str(uuid.uuid4()))
    api_key = settings.GOOGLE_PLACES_API_KEY
    endpoint = "https://maps.googleapis.com/maps/api/place/autocomplete/json"

    params = {
        "input": query,
        "key": api_key,
        "types": "geocode",
        "language": "en",
        "sessiontoken": session_token
    }

    try:
        # Make the request
        response = client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        # Handle Google API response status
        google_status = data.get("status", "")

        if google_status == "OK":
            suggestions = [
                {"description": place["description"], "place_id": place["place_id"]}
                for place in data.get("predictions", [])
            ]
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

    except httpx.RequestError:
        return Response(
            {"error": "Failed to connect to Google API."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except Exception:
        return Response(
            {"error": "An unexpected error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from django.db import IntegrityError
#
# @api_view(['POST'])
# def reset_usage_view(request):
#     try:
#         # Ensure only one entry is updated or created
#         api_usage, created = APIUsage.objects.get_or_create(
#             defaults={"request_count": 0}
#         )
#         if not created:
#             # If the record already exists, update the `request_count`
#             api_usage.request_count = 0
#             api_usage.save()
#
#         return Response(
#             {"message": "API usage successfully reset."},
#             status=200
#         )
#     except IntegrityError as e:
#         return Response(
#             {"error": "Error resetting API usage: " + str(e)},
#             status=500
#         )

