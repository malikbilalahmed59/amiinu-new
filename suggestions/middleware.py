from datetime import date
from .models import APIUsage

class APILoggingMiddleware:
    """
    Middleware to log API usage for address suggestions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for the address suggestions endpoint
        if request.path.startswith("/api/suggestions/address-suggestions/"):
            today = date.today()

            # Get or create the usage record for today
            usage, created = APIUsage.objects.get_or_create(date=today)

            # Increment the request count
            usage.increment_usage()

        response = self.get_response(request)
        return response
