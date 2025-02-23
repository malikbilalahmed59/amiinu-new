import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
# from .models import APIUsage

import uuid
import asyncio
import httpx

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Create a single, global AsyncClient to reuse connections (HTTP/2 if available).
# This avoids overhead of establishing a new TCP/TLS connection on every request.
# Make sure to manage the lifecycle if you're using it across the entire app.
async_client = httpx.AsyncClient(
    http2=True,       # Use HTTP/2 if supported by the server for multiplexing
    timeout=5.0,      # Fail fast if Google takes too long
    headers={
        "Accept-Encoding": "gzip, deflate",  # Request compressed response from Google
    }
)

@api_view(['GET'])
async def address_suggestions(request):
    """
    Fetch address suggestions from Google Places using async & connection pooling.
    """

    # 1. Get the query parameter
    query = request.GET.get('query', '')
    if not query:
        return Response({"error": "Query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Set up Google Places Autocomplete parameters
    session_token = request.GET.get('sessiontoken', str(uuid.uuid4()))
    api_key = settings.GOOGLE_PLACES_API_KEY
    endpoint = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": query,
        "key": api_key,
        "types": "geocode",
        "language": "en",
        "sessiontoken": session_token,  # helps Google optimize repeated calls
    }

    try:
        # 3. Make the async request to Google
        response = await async_client.get(endpoint, params=params)
        data = response.json()

        # 4. Check Google’s response status
        #    Could be "OK", "ZERO_RESULTS", "OVER_QUERY_LIMIT", etc.
        if data.get("status") != "OK":
            # Return Google's error_message if present
            return Response(
                {"error": data.get("error_message", data.get("status", "Unknown error"))},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Build your suggestions response
        suggestions = [
            {
                "description": place["description"],
                "place_id": place["place_id"]
            }
            for place in data.get("predictions", [])
        ]

        # 6. Return final JSON response
        #    GzipMiddleware in Django will compress if large enough
        return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)

    except httpx.RequestError as e:
        # Network error, DNS error, etc.
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

