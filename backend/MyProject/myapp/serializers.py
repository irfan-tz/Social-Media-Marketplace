from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth.models import User
from .models import Message, Profile, UserBlock, ReportCategory, UserReport, AdminAction, Friendship
from django.utils import timezone
from django.db.models import Q


############################ LOGIN / USER-MANAGEMENT ############################

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    last_interaction = serializers.DateTimeField(read_only=True)
    friendship_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture_url', 'last_interaction', 'friendship_status']

    def get_profile_picture_url(self, obj):
        # Try to get the profile image URL from the related profile
        try:
            profile = obj.profile
            if profile.profile_picture:
                return profile.profile_picture.url
        except Exception:
            pass
        # Fallback: return a default avatar URL (e.g., DiceBear avatar)
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={obj.username}"

    def get_friendship_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        friendship = Friendship.objects.filter(
            Q(sender=request.user, receiver=obj) |
            Q(sender=obj, receiver=request.user)
        ).first()

        if friendship:
            return {
                'status': friendship.status,
                'is_sender': friendship.sender == request.user
            }
        return None

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

from rest_framework import serializers
from django.conf import settings
import os
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ProfileFullSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    profile_picture_url = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()
    verification_document = serializers.FileField(required=False, allow_null=True)  # Added field
    user_id = serializers.IntegerField(source='user.id')

    class Meta:
        model = Profile
        fields = [
            'user_id', 'full_name', 'username', 'email', 'bio',
            'profile_picture', 'profile_picture_url',
            'is_verified', 'verification_document'  # Include it here
        ]

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture:
            return None
        try:
            return obj.profile_picture.url
        except Exception as e:
            logger.error(f"Error generating profile picture URL for user {obj.user.id}: {e}")
            return None

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            instance.user.username = user_data.get('username', instance.user.username)
            instance.user.email = user_data.get('email', instance.user.email)
            instance.user.save()

        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.bio = validated_data.get('bio', instance.bio)

        if 'profile_picture' in validated_data:
            if instance.profile_picture:
                instance.profile_picture.delete(save=False)
            instance.profile_picture = validated_data.get('profile_picture')

        if 'verification_document' in validated_data:
            if instance.verification_document:
                instance.verification_document.delete(save=False)
            instance.verification_document = validated_data.get('verification_document')
            instance.verification_submitted_at = timezone.now()

        instance.save()
        return instance



# Redundant?
# Profile Serializer
# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = ['profile_picture']

# Custom JWT Token Serializer
class TryLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        credentials = {
            'username': attrs.get("username"),
            'password': attrs.get("password")
        }
        return super().validate(credentials)

# User Registration Serializer
import re
import dns.resolver  # Ensure you have dnspython installed: pip install dnspython
from rest_framework import serializers
from django.contrib.auth.models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    verification_document = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'verification_document']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        # Extract domain from email
        try:
            domain = value.split('@')[1]
        except IndexError:
            raise serializers.ValidationError("Invalid email format.")

        # Define trusted patterns for email domains
        trusted_patterns = [
            r'^(.*\.)?gmail\.com$',         # Matches "gmail.com" and subdomains
            r'^(.*\.)?outlook\.com$',        # Matches "outlook.com" and subdomains
            r'^(.*\.)?hotmail\.com$',        # Matches "hotmail.com" and subdomains
            r'^(.*\.)?live\.com$',           # Matches "live.com" and subdomains
            r'^(.*\.)?(yahoo|ymail)\.com$',   # Matches "yahoo.com", "ymail.com", and subdomains
            r'^(.*\.)?protonmail\.com$',      # Matches "protonmail.com" and subdomains
            r'^[a-z0-9-]+\.ac\.[a-z]{2,}$'     # Educational institutions (e.g., iiitd.ac.in)
        ]

        # Check if the domain matches any trusted pattern
        if any(re.match(pattern, domain, re.IGNORECASE) for pattern in trusted_patterns):
            # For non-educational domains, check if they have valid MX records.
            if 'ac.' not in domain:
                if not self.has_valid_mx(domain):
                    raise serializers.ValidationError(
                        "This email domain doesn't appear to have valid email servers."
                    )
        else:
            raise serializers.ValidationError("Email provider is not trusted. Please use a valid email address.")

        # Check if the email is already registered
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")

        return value

    def has_valid_mx(self, domain):
        """
        Check if the email domain has valid MX records.
        For known providers like live.com or hotmail.com, if DNS lookup fails,
        you may opt to return True.
        """
        try:
            records = dns.resolver.resolve(domain, 'MX')
            return bool(records)
        except dns.resolver.NoAnswer:
            return False
        except Exception:
            # For domains we trust, like live.com or hotmail.com, return True if lookup fails
            if domain.lower() in ['live.com', 'hotmail.com']:
                return True
            return False

    def create(self, validated_data):
        validated_data.pop('verification_document', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        import time
        time.sleep(0.1)  # Give signals a brief moment to complete
        return user

############################ MESSAGING ############################

from django.urls import reverse
import mimetypes
class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    decrypted_content = serializers.SerializerMethodField()
    attachment = serializers.FileField(required=False)
    attachment_url = serializers.SerializerMethodField()
    attachment_content_type = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_username', 'receiver', 'receiver_username',
            'content', 'decrypted_content', 'attachment', 'attachment_url',
            'attachment_content_type', 'timestamp'
        ]
        extra_kwargs = {
            'sender': {'read_only': True},
            'content': {'write_only': True, 'required': False},
        }

    def get_decrypted_content(self, obj):
        try:
            # Handle attachment-only messages
            if not obj.content and obj.attachment:
                return ""
            return obj.get_decrypted_content()
        except Exception as e:
            print(f"Decryption error for message {obj.id}: {str(e)}")
            # If message has an attachment but decryption fails, don't show error
            if obj.attachment:
                return ""
            return "Error decrypting message"

    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            url = reverse('serve_decrypted_file', args=[obj.id])
            return request.build_absolute_uri(url) if request else url
        return None

    def get_attachment_content_type(self, obj):
        if obj.attachment:
            # If your Message model stores a content type, use that
            if hasattr(obj, 'attachment_content_type') and obj.attachment_content_type:
                return obj.attachment_content_type
            # Otherwise, try to guess based on the file's name
            mime_type, _ = mimetypes.guess_type(obj.attachment.name)
            return mime_type
        return None

    def create(self, validated_data):
        attachment = validated_data.pop('attachment', None)

        message = Message(
            sender=validated_data['sender'],
            receiver=validated_data['receiver'],
            content=validated_data.get('content', '')
        )

        # Store the attachment to be encrypted during save if provided
        if attachment:
            message._attachment_to_encrypt = attachment

        message.save()
        return message


from .models import ChatGroup, ChatGroupMessage
class ChatGroupSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True
    )
    created_by = serializers.ReadOnlyField(source='created_by.id')
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatGroup
        fields = ['id', 'name', 'members', 'created_by', 'created_at', 'members_count']

    def get_members_count(self, obj):
        return obj.members.count()

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        group = ChatGroup.objects.create(**validated_data)

        # Add the creator
        request_user = self.context['request'].user
        group.members.add(request_user)

        # Add selected members
        for m in members:
            group.members.add(m)

        return group


class ChatGroupMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    decrypted_content = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatGroupMessage
        fields = ['id', 'chat_group', 'sender', 'sender_username', 'content', 'decrypted_content', 'timestamp', 'profile_picture_url']
        extra_kwargs = {
            'sender': {'read_only': True},
            'content': {'write_only': True},
        }

    def get_decrypted_content(self, obj):
        return obj.get_decrypted_content()

    def get_profile_picture_url(self, obj):
        if hasattr(obj.sender, 'profile') and obj.sender.profile.profile_picture:
            return obj.sender.profile.profile_picture.url
        return None

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    decrypted_content = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatGroupMessage
        fields = [
            'id',
            'chat_group',  # expect chat_group in payload
            'sender',
            'sender_username',
            'content',
            'decrypted_content',
            'timestamp',
            'profile_picture_url'
        ]
        extra_kwargs = {
            'sender': {'read_only': True},
            'content': {'write_only': True},
        }

    def get_decrypted_content(self, obj):
        return obj.get_decrypted_content()

    def get_profile_picture_url(self, obj):
        if hasattr(obj.sender, 'profile') and obj.sender.profile.profile_picture:
            return obj.sender.profile.profile_picture.url
        return None

    def validate_chat_group(self, value):
        # Optionally, validate that the chat group exists and the user is a member
        request = self.context.get("request")
        if request and request.user not in value.members.all():
            raise serializers.ValidationError("You are not a member of this chat group.")
        return value

    def create(self, validated_data):
        return ChatGroupMessage.objects.create(**validated_data)

class UserBlockSerializer(serializers.ModelSerializer):
    blocked_username = serializers.ReadOnlyField(source='blocked.username')

    class Meta:
        model = UserBlock
        fields = ['id', 'blocked', 'blocked_username', 'created_at']
        read_only_fields = ['blocker', 'created_at']

    def validate_blocked(self, value):
        if not value:
            raise serializers.ValidationError("Blocked user is required")

        if self.context['request'].user.id == value.id:
            raise serializers.ValidationError("You cannot block yourself")

        # Check if already blocked
        if UserBlock.objects.filter(blocker=self.context['request'].user, blocked=value).exists():
            raise serializers.ValidationError("You have already blocked this user")

        return value

class ReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCategory
        fields = ['id', 'name', 'description']

class UserReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.ReadOnlyField(source='reporter.username')
    reported_username = serializers.ReadOnlyField(source='reported_user.username')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = UserReport
        fields = [
            'id', 'reporter', 'reporter_username',
            'reported_user', 'reported_username',
            'category', 'category_name', 'description',
            'evidence', 'created_at', 'status'
        ]
        read_only_fields = ['reporter', 'status']

    def validate(self, data):
        # Prevent users from reporting themselves
        if self.context['request'].user.id == data['reported_user'].id:
            raise serializers.ValidationError("You cannot report yourself.")

        # Check if the user has already reported this person for the same category
        existing_report = UserReport.objects.filter(
            reporter=self.context['request'].user,
            reported_user=data['reported_user'],
            category=data['category'],
            status__in=['pending', 'reviewing']
        ).exists()

        if existing_report:
            raise serializers.ValidationError(
                "You have already reported this user for this reason. Wait for admins to review."
            )

        return data

class AdminActionSerializer(serializers.ModelSerializer):
    admin_username = serializers.ReadOnlyField(source='admin.username')

    class Meta:
        model = AdminAction
        fields = ['id', 'report', 'admin', 'admin_username', 'action', 'notes', 'created_at']
        read_only_fields = ['admin']

class AdminReportDetailSerializer(serializers.ModelSerializer):
    """Extended report serializer with admin actions for admin dashboard"""
    reporter_username = serializers.ReadOnlyField(source='reporter.username')
    reporter_email = serializers.ReadOnlyField(source='reporter.email')
    reported_username = serializers.ReadOnlyField(source='reported_user.username')
    reported_email = serializers.ReadOnlyField(source='reported_user.email')
    category_name = serializers.ReadOnlyField(source='category.name')
    admin_actions = AdminActionSerializer(many=True, read_only=True)

    class Meta:
        model = UserReport
        fields = [
            'id', 'reporter', 'reporter_username', 'reporter_email',
            'reported_user', 'reported_username', 'reported_email',
            'category', 'category_name', 'description',
            'evidence', 'created_at', 'status',
            'admin_notes', 'admin_actions'
        ]

class UserBlockSerializer(serializers.ModelSerializer):
    blocked_username = serializers.ReadOnlyField(source='blocked.username')

    class Meta:
        model = UserBlock
        fields = ['id', 'blocked', 'blocked_username', 'created_at']
        read_only_fields = ['blocker']

    def validate(self, data):
        # Prevent users from blocking themselves
        if self.context['request'].user.id == data['blocked'].id:
            raise serializers.ValidationError("You cannot block yourself.")
        return data

class ReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCategory
        fields = ['id', 'name', 'description']

class UserReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.ReadOnlyField(source='reporter.username')
    reported_username = serializers.ReadOnlyField(source='reported_user.username')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = UserReport
        fields = [
            'id', 'reporter', 'reporter_username',
            'reported_user', 'reported_username',
            'category', 'category_name', 'description',
            'evidence', 'created_at', 'status'
        ]
        read_only_fields = ['reporter', 'status']

    def validate(self, data):
        # Prevent users from reporting themselves
        if self.context['request'].user.id == data['reported_user'].id:
            raise serializers.ValidationError("You cannot report yourself.")

        # Check if the user has already reported this person for the same category
        existing_report = UserReport.objects.filter(
            reporter=self.context['request'].user,
            reported_user=data['reported_user'],
            category=data['category'],
            status__in=['pending', 'reviewing']
        ).exists()

        if existing_report:
            raise serializers.ValidationError(
                "You have already reported this user for this reason. Wait for admins to review."
            )

        return data
class FriendshipSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    sender_profile_pic = serializers.SerializerMethodField()
    receiver_profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ['id', 'sender', 'sender_username', 'sender_profile_pic',
                  'receiver', 'receiver_username', 'receiver_profile_pic',
                  'status', 'created_at']
        read_only_fields = ['sender', 'created_at']

    def get_sender_profile_pic(self, obj):
        return obj.sender.profile.profile_picture.url if obj.sender.profile.profile_picture else None

    def get_receiver_profile_pic(self, obj):
        return obj.receiver.profile.profile_picture.url if obj.receiver.profile.profile_picture else None
    

