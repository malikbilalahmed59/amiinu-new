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

# Use a synchronous client instead of an async client
client = httpx.Client(
    timeout=5.0,
    headers={"Accept-Encoding": "gzip, deflate"},
)


@api_view(['GET'])
def address_suggestions(request):
    """Fetch address suggestions from Google Places API (Synchronous Version)."""

    query = request.GET.get('query', '')
    if not query:
        return Response({"error": "Query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

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
        # Make the synchronous request
        response = client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            return Response({"error": data.get("error_message", "Unknown error.")}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = [
            {
                "description": place["description"],
                "place_id": place["place_id"]
            } for place in data.get("predictions", [])
        ]

        return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)

    except httpx.RequestError as e:
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

