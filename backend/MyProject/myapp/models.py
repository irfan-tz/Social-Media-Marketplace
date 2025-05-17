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

    public_key = models.TextField(null=True, blank=True)
    private_key = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Simply sync email and username with the linked user model.
        if self.user:
            self.email = self.user.email
            self.username = self.user.username

        # Generate key pair if not exists
        if not self.public_key or not self.private_key:
            from .crypto_utils import generate_key_pair
            public_key, private_key = generate_key_pair()
            self.public_key = public_key
            self.private_key = private_key

        # Handle verification document encryption
        if self.verification_document and not self.pk:  # New document being uploaded
            try:
                # Read the document
                self.verification_document.open()
                file_content = self.verification_document.read()
                self.verification_document.close()

                # Encrypt the content
                encrypted_content = encrypt_with_public_key(
                    file_content.decode('latin-1'),
                    self.public_key
                )

                # Save encrypted content back to the file
                ext = os.path.splitext(self.verification_document.name)[1]
                encrypted_filename = f"encrypted_{uuid.uuid4().hex}{ext}"

                # Save the encrypted content
                self.verification_document.save(
                    encrypted_filename,
                    ContentFile(encrypted_content.encode()),
                    save=False
                )
            except Exception as e:
                pass

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

    def encrypt_verification_document(self, file_content):
        """Encrypt verification document with user's public key"""
        if not self.public_key:
            return None
        try:
            encrypted_content = encrypt_with_public_key(file_content, self.public_key)
            return encrypted_content
        except Exception as e:
            return None

    def decrypt_verification_document(self, encrypted_content):
        """Decrypt verification document with user's private key"""
        if not self.private_key:
            return None
        try:
            decrypted_content = decrypt_with_private_key(encrypted_content, self.private_key)
            return decrypted_content
        except Exception as e:
            return None

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

from django.core.files.base import ContentFile
from .crypto_utils import generate_key_pair, encrypt_with_public_key, decrypt_with_private_key
import uuid

import logging
logger = logging.getLogger(__name__)

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
    original_filename = models.CharField(max_length=255, blank=True, null=True)  # Store original filename
    attachment_content_type = models.CharField(max_length=100, blank=True, null=True)  # Store MIME type
    timestamp = models.DateTimeField(auto_now_add=True)
    is_encrypted = models.BooleanField(default=False)

    # Encryption logic for text content
    def encrypt_message(self, message):
        return cipher_suite.encrypt(message.encode()).decode()

    def decrypt_message(self, content=None):
        """Decrypt content with Fernet.
        If content is provided, decrypt that content.
        Otherwise, decrypt self.content.
        """
        content_to_decrypt = content if content is not None else self.content
        return cipher_suite.decrypt(content_to_decrypt.encode()).decode()

    # New methods for file encryption/decryption
    def encrypt_file(self, file):
        # Read the file content
        file_content = file.read()
        # Encrypt the content
        encrypted_content = cipher_suite.encrypt(file_content)
        # Generate a random filename
        ext = os.path.splitext(file.name)[1].lower()
        encrypted_filename = f"{uuid.uuid4().hex}{ext}"
        # Store the original filename and content type
        self.original_filename = file.name
        self.attachment_content_type = getattr(file, 'content_type', None)
        # Return a ContentFile with encrypted content
        return ContentFile(encrypted_content, name=encrypted_filename)



    def get_decrypted_attachment(self):
        if not self.attachment:
            return None
        try:
            self.attachment.open(mode='rb')
            encrypted_content = self.attachment.read()
            decrypted_content = cipher_suite.decrypt(encrypted_content)
            return ContentFile(decrypted_content, name=self.original_filename or self.attachment.name)
        except Exception as e:
            logger.error(f"Error decrypting file: {e}", exc_info=True)
            return None
        finally:
            self.attachment.close()

    def save(self, *args, **kwargs):
        # Check if this is a new instance
        is_new = self.pk is None

        # Handle content encryption for new messages with content
        if is_new and self.content:
            try:
                # First encrypt with Fernet
                fernet_encrypted = self.encrypt_message(self.content)

                # Then try to encrypt with receiver's public key
                receiver_public_key = self.receiver.profile.public_key
                if receiver_public_key:
                    self.content = encrypt_with_public_key(fernet_encrypted, receiver_public_key)
                    self.is_encrypted = True
                else:
                    # If no public key available, just use Fernet encryption
                    self.content = fernet_encrypted
                    self.is_encrypted = False
            except Exception as e:
                # Fallback to just Fernet encryption
                self.content = self.encrypt_message(self.content)
                self.is_encrypted = False
        # For attachment-only messages (no content), ensure content field isn't NULL
        elif is_new and not self.content and hasattr(self, '_attachment_to_encrypt'):
            self.content = ""

        # Handle file encryption for new instances with attachment
        if is_new and hasattr(self, '_attachment_to_encrypt') and self._attachment_to_encrypt:
            self.attachment = self.encrypt_file(self._attachment_to_encrypt)
            delattr(self, '_attachment_to_encrypt')

        super().save(*args, **kwargs)

    def get_decrypted_content(self):
        try:
            # If the message is attachment-only with no text content, return empty string
            if not self.content and self.attachment:
                return ""

            if self.is_encrypted:
                # New messages (double encrypted)
                # First decrypt with private key
                private_key = self.receiver.profile.private_key
                fernet_encrypted = decrypt_with_private_key(self.content, private_key)
                # Then decrypt with Fernet
                return self.decrypt_message(fernet_encrypted)
            else:
                # Old messages (only Fernet encrypted)
                return self.decrypt_message(self.content)
        except Exception as e:
            # If this is an attachment-only message, return empty string instead of error
            if self.attachment and not self.content:
                return ""
            return "Error decrypting message"

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

class UserBlock(models.Model):
    """Records when a user blocks another user"""
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        verbose_name = "User Block"
        verbose_name_plural = "User Blocks"

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"

class ReportCategory(models.Model):
    """Categories for user reports"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Report Category"
        verbose_name_plural = "Report Categories"

    def __str__(self):
        return self.name

class UserReport(models.Model):
    """Records when a user reports another user"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved - No Action'),
        ('action_taken', 'Resolved - Action Taken')
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_filed')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    category = models.ForeignKey(ReportCategory, on_delete=models.CASCADE)
    description = models.TextField()
    evidence = models.FileField(upload_to='report_evidence/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "User Report"
        verbose_name_plural = "User Reports"
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id}: {self.reporter.username} reported {self.reported_user.username}"

class AdminAction(models.Model):
    """Records admin actions taken on reports"""
    ACTION_CHOICES = [
        ('reviewed', 'Reviewed - No Action'),
        ('warning', 'Warning Issued'),
        ('temp_ban', 'Temporary Ban'),
        ('perm_ban', 'Permanent Ban')
    ]

    report = models.ForeignKey(UserReport, on_delete=models.CASCADE, related_name='admin_actions')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_actions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin Action"
        verbose_name_plural = "Admin Actions"
        ordering = ['-created_at']

    def __str__(self):
        return f"Action on Report #{self.report.id} by {self.admin.username}: {self.action}"

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['sender', 'receiver']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"
