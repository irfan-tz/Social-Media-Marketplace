from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a profile when a new user is created
    or ensure a profile exists for existing users
    """
    if created:
        # Create profile for newly created users
        Profile.objects.create(user=instance)
    else:
        # For existing users, create profile if it doesn't exist
        try:
            instance.profile
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Ensure profile is saved when user is saved
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)