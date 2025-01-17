# models.py in the suggestions app
from django.db import models
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

class APIUsage(models.Model):
    date = models.DateField(default=now)  # Date of usage record
    request_count = models.PositiveIntegerField(default=0)  # Total requests made
    reset_date = models.DateField(null=True, blank=True)  # Next reset date

    def __str__(self):
        return f"Usage on {self.date}: {self.request_count} requests"

    def increment_usage(self, count=1):
        """Increment the usage count."""
        self.request_count += count
        self.save()

    def reset_usage(self):
        """Reset usage to zero."""
        self.request_count = 0
        self.reset_date = now().date().replace(day=1) + relativedelta(months=1)  # Next month's first day
        self.save()
