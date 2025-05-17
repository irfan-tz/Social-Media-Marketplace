from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Message, Profile
from django.utils import timezone 

############################ LOGIN / USER-MANAGEMENT ############################

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    last_interaction = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture_url', 'last_interaction']

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

    class Meta:
        model = Profile
        fields = [
            'full_name', 'username', 'email', 'bio', 
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
class UserRegistrationSerializer(serializers.ModelSerializer):
    verification_document = serializers.FileField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'verification_document']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    # def create(self, validated_data):
    #     verification_file = validated_data.pop('verification_document')
    #     user = User(
    #         username=validated_data['username'],
    #         email=validated_data['email']
    #     )
    #     # Create profile with verification document
    #     # profile = Profile.objects.create(
    #     #     user=user,
    #     #     verification_document=verification_file,
    #     #     verification_submitted_at=timezone.now()
    #     # )
    #     user.set_password(validated_data['password'])
    #     user.save()
    #     # Profile creation could be handled automatically via signals
    #     return user
    def create(self, validated_data):
        verification_file = validated_data.pop('verification_document')
        
        # Create user (this will trigger the signal to create profile)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Wait a brief moment for signal to complete
        import time
        time.sleep(0.1)  # 100ms delay to ensure signal completes
        
        # Now update the auto-created profile
        user.profile.verification_document = verification_file
        user.profile.verification_submitted_at = timezone.now()
        user.profile.save()
        
        return user

############################ MESSAGING ############################

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    decrypted_content = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'sender_username',
            'receiver',
            'receiver_username',
            'content',
            'decrypted_content',
            'attachment',
            'attachment_url',
            'timestamp'
        ]
        extra_kwargs = {
            'sender': {'read_only': True},
            'content': {'write_only': True, 'required': False},
        }

    def get_decrypted_content(self, obj):
        try:
            return obj.get_decrypted_content()
        except Exception:
            return "Error decrypting message"

    def get_attachment_url(self, obj):
        if obj.attachment:
            return obj.attachment.url
        return None

    def create(self, validated_data):
        message = Message.objects.create(
            sender=validated_data['sender'],
            receiver=validated_data['receiver'],
            content=validated_data.get('content', ''),
            attachment=validated_data.get('attachment', None)
        )
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

