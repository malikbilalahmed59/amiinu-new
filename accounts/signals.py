from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Automatically create a corresponding Profile whenever
    a new user (CustomUser) instance is created.
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """
    Whenever the User (CustomUser) is saved, also save the
    associated Profile (if it exists).
    """
    # This assumes the Profile was created (above) on user creation.
    # If you need to handle a case where the profile might not exist,
    # you could check if hasattr(instance, 'profile').
    instance.profile.save()