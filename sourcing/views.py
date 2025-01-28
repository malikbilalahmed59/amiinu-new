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
        Override to standardize error response format and include field names.
        """
        response = super().handle_exception(exc)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            if isinstance(response.data, dict):
                # Extract error messages and include field names in the response
                errors = {}
                for field, error_list in response.data.items():
                    errors[field] = " ".join([str(error) for error in error_list])
                response.data = {"message": errors}
            else:
                response.data = {"message": "Invalid input."}
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            response.data = {"message": "The requested resource was not found."}
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            response.data = {"message": "You do not have permission to perform this action."}
        else:
            response.data = {"message": "An unexpected error occurred. Please try again."}
        return response

