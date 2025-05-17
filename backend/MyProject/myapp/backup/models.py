from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from cryptography.fernet import Fernet

############################ PROFILE ############################
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
import os
def validate_file_size(value):
    filesize = value.size
    
    if filesize > 5 * 1024 * 1024:  # 5 MB
        raise ValidationError("The maximum file size that can be uploaded is 5MB")

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported file extension.')

def validate_image_dimensions(value):
    width, height = get_image_dimensions(value)
    if width > 1920 or height > 1080:
        raise ValidationError('Image dimensions should not exceed 1920x1080 pixels.')

from django.utils.deconstruct import deconstructible
from django.core.files.storage import default_storage

import os
from django.db import models
from django.contrib.auth.models import User

@deconstructible
class ProfilePictureUploadPath:
    def __init__(self, base_path="profile_pics/"):
        self.base_path = base_path
    
    
    def __call__(self, instance, filename):
        """
        Generate a unique filename based on user ID
        
        Args:
            instance: The Profile model instance
            filename: Original filename
        
        Returns:
            str: New filename with path
        """
        # Get file extension
        ext = os.path.splitext(filename)[1]
        
        # Generate new filename with user ID
        new_filename = f"profile_{instance.user.id}{ext}"
        
        # Full path including base directory
        return os.path.join(self.base_path, new_filename)


class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        primary_key=True,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    # New fields: username and email are stored redundantly for quick access and uniqueness
    username = models.CharField(max_length=150, default='')
    email = models.EmailField(default='')
    full_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        default=''
    )
    bio = models.TextField(
        blank=True, 
        null=True,
        default=''
    )
    profile_picture = models.ImageField(
        upload_to=ProfilePictureUploadPath(), 
        null=True, 
        blank=True
    )
    is_verified = models.BooleanField(default=False)
    verification_document = models.FileField(
        upload_to='verification_docs/%Y/%m/%d/',  # Add date-based organization,
        null=True,
        blank=True,
        validators=[
            validate_file_size,  
        ]
    )
    
    verification_submitted_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Simply sync email and username with the linked user model.
        if self.user:
            self.email = self.user.email
            self.username = self.user.username

        # If updating profile picture, delete the old one if necessary
        if self.pk:
            try:
                old_instance = Profile.objects.get(pk=self.pk)
                if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                    old_instance.profile_picture.delete(save=False)
            except Profile.DoesNotExist:
                pass
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def delete(self, *args, **kwargs):
        if self.profile_picture:
            self.profile_picture.delete(save=False)
        super().delete(*args, **kwargs)

class ChatGroup(models.Model):
    name = models.CharField(max_length=255)
    # Rename reverse accessor on User to "chat_groups"
    members = models.ManyToManyField(User, related_name="chat_groups")
    # Use a more descriptive related_name for the creator
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="created_chat_groups"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

############################ MESSAGES ############################

# Generate a key for encryption (store this securely in settings.py)
cipher_suite = Fernet(settings.ENCRYPTION_KEY)


def validate_attachment(file):
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm', '.ogg']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError("Unsupported file extension.")
    # Optionally, enforce a file size limit here
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        raise ValidationError("File size exceeds 10MB.")

class Message(models.Model):
    sender = models.ForeignKey(
        User, related_name='sent_messages', on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User, related_name='received_messages', on_delete=models.CASCADE
    )
    content = models.TextField(blank=True)  # Allow blank if attachment is sent
    attachment = models.FileField(
        upload_to='message_attachments/',
        blank=True,
        null=True,
        validators=[validate_attachment]
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    # Encryption logic remains as before for content
    def encrypt_message(self, message):
        return cipher_suite.encrypt(message.encode()).decode()

    def decrypt_message(self):
        return cipher_suite.decrypt(self.content.encode()).decode()

    def save(self, *args, **kwargs):
        if self.content and not self.id:  # Encrypt only on creation
            self.content = self.encrypt_message(self.content)
        super().save(*args, **kwargs)

    def get_decrypted_content(self):
        try:
            return self.decrypt_message()
        except Exception:
            return ""
    
    class Meta:
        ordering = ['-timestamp']


class ChatGroupMessage(models.Model):
    chat_group = models.ForeignKey(
        ChatGroup,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()  # This will be encrypted
    timestamp = models.DateTimeField(auto_now_add=True)

    def encrypt_message(self, message):
        return cipher_suite.encrypt(message.encode()).decode()

    def decrypt_message(self):
        return cipher_suite.decrypt(self.content.encode()).decode()

    def save(self, *args, **kwargs):
        if not self.id:
            self.content = self.encrypt_message(self.content)
        super().save(*args, **kwargs)

    def get_decrypted_content(self):
        try:
            return self.decrypt_message()
        except Exception:
            return "Error decrypting message"

    class Meta:
        ordering = ['timestamp']

