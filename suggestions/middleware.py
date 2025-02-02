# from datetime import date
# from .models import APIUsage
#
# class APILoggingMiddleware:
#     """
#     Middleware to log API usage for address suggestions.
#     """
#
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         if request.path.startswith("/api/suggestions/address-suggestions/"):
#             usage, created = APIUsage.objects.get_or_create(id=1, defaults={"request_count": 0})
#
#             usage.increment_usage()
#
#         response = self.get_response(request)
#         return response
