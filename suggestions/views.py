import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import APIUsage

@api_view(['GET'])
def address_suggestions(request):
    query = request.GET.get('query', '')  # Address input from the user
    if not query:
        return Response({"error": "Query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    api_key = settings.GOOGLE_PLACES_API_KEY
    endpoint = "https://maps.googleapis.com/maps/api/place/autocomplete/json"

    params = {
        "input": query,
        "key": api_key,
        "types": "geocode",  # Restrict to address results
        "language": "en",   # Language for suggestions
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if data.get("status") != "OK":
            return Response({"error": data.get("error_message", "Unknown error.")}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = [
            {
                "description": place["description"],
                "place_id": place["place_id"],
            }
            for place in data.get("predictions", [])
        ]
        return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def reset_usage_view(request):
    APIUsage.objects.update(request_count=0)
    return Response({"message": "API usage successfully reset."}, status=200)