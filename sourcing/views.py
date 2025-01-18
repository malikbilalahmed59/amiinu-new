from django.db.models import Count
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import SourcingRequest
from .serializers import SourcingRequestSerializer


class SourcingRequestViewSet(ModelViewSet):
    serializer_class = SourcingRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only sourcing requests created by the logged-in user
        return SourcingRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically associate the logged-in user with the sourcing request
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Aggregate data for status summary
        status_counts = (
            queryset.values('status')
            .annotate(total=Count('status'))
        )
        summary = {choice[0]: 0 for choice in SourcingRequest.STATUS_CHOICES}
        for entry in status_counts:
            summary[entry['status']] = entry['total']

        # Combine sourcing requests and summary in the response
        return Response({
            'sourcing_requests': serializer.data,
            'status_summary': summary,
        })

    def handle_exception(self, exc):
        """
        Override to standardize error response format.
        """
        response = super().handle_exception(exc)
        if isinstance(response.data, dict):
            response.data = {"message": response.data.get("detail", str(exc))}
        else:
            response.data = {"message": "An unexpected error occurred. Please try again."}
        return response
