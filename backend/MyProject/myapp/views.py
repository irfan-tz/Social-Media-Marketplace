from django.db.models import Q
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .models import Message, Profile, ReportCategory, UserBlock, Friendship, UserReport
from .serializers import MessageSerializer, UserRegistrationSerializer, UserSerializer, UserBlockSerializer, FriendshipSerializer, ReportCategorySerializer, UserReportSerializer
from rest_framework.parsers import MultiPartParser, FormParser
# Add at the top of views.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView



# Add these imports at the top of views.py
from django.db.models import Q
from .models import Friendship  # Add this with other model imports
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import permissions, status
from rest_framework.response import Response


############################ REGISTRATION / LOGIN/LOGOUT ############################
from rest_framework.response import Response
from django.conf import settings
from rest_framework import status

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            # Handle potential IntegrityError or other exceptions
            return Response({
                'error': 'Registration failed',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import TryLoginSerializer
class TryLoginDumbWitView(TokenObtainPairView):
    """
    Modified to set JWT cookies securely
    """
    serializer_class = TryLoginSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                'error': 'Invalid credentials',
                'details': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Get tokens
        refresh = serializer.validated_data.get('refresh')
        access = serializer.validated_data.get('access')

        # Create response
        response = Response(status=status.HTTP_200_OK)

        # Set cookies with enhanced security
        response.set_cookie(
            key='access_token',
            value=access,
            httponly=True,
            secure=True,  # HTTPS only
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
        )
        return response

from rest_framework_simplejwt.views import TokenRefreshView
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            # Attempt to get refresh token from cookies
            refresh_token = request.COOKIES.get('refresh_token')

            # If no refresh token in cookies, return unauthorized
            if not refresh_token:
                return Response({
                    'refreshed': False,
                    'error': 'No refresh token found'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Add refresh token to request data
            request.data['refresh'] = refresh_token

            response = super().post(request, *args, **kwargs)

            access_token = response.data.get('access')

            res = Response({'refreshed': True}, status=status.HTTP_200_OK)
            res.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True,
                samesite='Lax',
                path='/'
            )

            return res

        except Exception as e:
            return Response({
                'refreshed': False,
                'error': 'Token refresh failed'
            }, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.views import APIView
from .authentication import CookiesJWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
class LogoutView(APIView):
    authentication_classes = [CookiesJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            response = Response({"logout": True}, status=status.HTTP_200_OK)

            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception as token_error:
                    print(f"Token blacklisting error: {token_error}")

            response.delete_cookie('access_token', path='/', samesite='Lax')
            response.delete_cookie('refresh_token', path='/', samesite='Lax')

            return response

        except Exception as e:
            return Response({
                'logout': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


############################ MESSAGING ############################

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Show only messages where current user is sender OR receiver
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).order_by('-timestamp')

    def perform_create(self, serializer):
        receiver = serializer.validated_data['receiver']

        # Check if users are friends
        if not Friendship.objects.filter(
            Q(sender=self.request.user, receiver=receiver, status='accepted') |
            Q(sender=receiver, receiver=self.request.user, status='accepted')
        ).exists():
            raise PermissionDenied("You can only message friends")

        serializer.save(sender=self.request.user)

class MessageDetailView(generics.RetrieveAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]


from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
import os

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound

class ServeDecryptedFileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        message = get_object_or_404(
            Message,
            Q(sender=request.user) | Q(receiver=request.user),
            id=message_id,
        )
        if not message.attachment:
            raise NotFound("No attachment found")
        decrypted_file = message.get_decrypted_attachment()
        if not decrypted_file:
            raise NotFound("Error decrypting file")

        response = HttpResponse(
            decrypted_file.read(),
            content_type=message.attachment_content_type or 'application/octet-stream'
        )
        filename = message.original_filename or os.path.basename(message.attachment.name)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


from .models import ChatGroup, ChatGroupMessage
from .serializers import ChatGroupSerializer, ChatGroupMessageSerializer, ChatMessageSerializer

# Retrieve a specific chat group (optional)
class ChatGroupDetailView(generics.RetrieveAPIView):
    queryset = ChatGroup.objects.all()
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class ChatGroupListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatGroup.objects.filter(members=self.request.user)

    def perform_create(self, serializer):
        # Fix: Creating a chat group should set the created_by field, not sender
        serializer.save(created_by=self.request.user)

# List and create messages for a specific chat group
class ChatGroupMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatGroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_group_id = self.kwargs.get('chat_group_id')
        return ChatGroupMessage.objects.filter(chat_group__id=chat_group_id)

    def perform_create(self, serializer):
        chat_group_id = self.kwargs.get('chat_group_id')
        chat_group = ChatGroup.objects.get(id=chat_group_id)
        serializer.save(sender=self.request.user, chat_group=chat_group)


# List and create chat messages (global endpoint with optional filtering)
class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter messages by a chat group if a query parameter is provided
        chat_group_id = self.request.query_params.get("chat_group")
        queryset = ChatGroupMessage.objects.all()

        if (chat_group_id):
            queryset = queryset.filter(chat_group__id=chat_group_id)

            # Only return messages from groups the user is a member of
            queryset = queryset.filter(chat_group__members=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


############################ PROFILE ############################

# Get profile details of the user
from .serializers import ProfileFullSerializer
class ProfileRetrieveView(generics.RetrieveAPIView):
    """
    Retrieve the authenticated user's profile details.
    """
    authentication_classes = [CookiesJWTAuthentication]
    serializer_class = ProfileFullSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        return self.request.user.profile

class ProfileUpdateView(generics.UpdateAPIView):
    """
    Update the authenticated user's profile details.
    """
    serializer_class = ProfileFullSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


from django.db.models import Max, Q
from django.db.models.functions import Greatest
class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        current_user = self.request.user
        qs = User.objects.exclude(id=current_user.id)

        qs = qs.annotate(
            last_sent=Max('sent_messages__timestamp', filter=Q(sent_messages__receiver=current_user)),
            last_received=Max('received_messages__timestamp', filter=Q(received_messages__sender=current_user))
        ).annotate(
            last_interaction=Greatest('last_sent', 'last_received')
        ).order_by('-last_interaction')

        return qs

# Add this new view
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

# View for retrieving a user's profile by username
class UserProfileView(generics.RetrieveAPIView):
    """
    Retrieve a user's profile by username.
    This view is protected and only accessible to authenticated users.
    """
    serializer_class = ProfileFullSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        username = self.kwargs.get('username')
        try:
            user = User.objects.get(username=username)
            return user.profile
        except User.DoesNotExist:
            raise NotFound(f"User with username '{username}' not found")

from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
import secrets

from rest_framework import serializers, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from .serializers import UserRegistrationSerializer  # Import your serializer

class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email using the registration serializer
        try:
            serializer = UserRegistrationSerializer(data={"email": email}, partial=True)
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            error_detail = e.detail
            # Normalize error detail to a dict with key 'email'
            if not isinstance(error_detail, dict):
                error_detail = {"email": error_detail}
            return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)

        # Rate limiting: Allow only 3 OTP requests per email per hour
        cache_key = f"otp_attempts_{email}"
        attempts = cache.get(cache_key, 0)
        if attempts >= 3:
            return Response(
                {"error": "Too many OTP requests. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        cache.set(cache_key, attempts + 1, 3600)  # 1 hour expiry

        otp = get_random_string(length=6, allowed_chars='0123456789')
        expiration_time = datetime.now() + timedelta(minutes=5)

        request.session['otp'] = otp
        request.session['email'] = email
        request.session['otp_expiration'] = expiration_time.isoformat()

        send_mail(
            "Your OTP Code",
            f"Your OTP code is {otp}. It will expire in 5 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        otp = request.data.get("otp")
        email = request.data.get("email")

        if not otp or not email:
            return Response({"error": "OTP and email are required"}, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = request.session.get('otp')
        stored_email = request.session.get('email')
        otp_expiration = request.session.get('otp_expiration')

        # Check if OTP is expired
        if not otp_expiration or datetime.fromisoformat(otp_expiration) < datetime.now():
            return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP and email match using constant-time comparison
        if secrets.compare_digest(stored_otp, otp) and secrets.compare_digest(stored_email, email):
            # Invalidate the OTP after successful verification
            del request.session['otp']
            del request.session['email']
            del request.session['otp_expiration']

            # Regenerate session ID to prevent session fixation
            request.session.cycle_key()

            return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)

        # Implement failed attempt tracking
        cache_key = f"otp_verify_attempts_{email}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, 3600)  # 1 hour expiry

        if attempts >= 5:
            # Lock verification for this email for 30 minutes
            cache.set(f"otp_verify_locked_{email}", True, 1800)
            return Response({"error": "Too many failed attempts. Try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response({"error": "Invalid OTP or email"}, status=status.HTTP_400_BAD_REQUEST)


class RequestAccountDeletionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        email = user.email

        # Generate OTP
        otp = get_random_string(length=6, allowed_chars='0123456789')
        expiration_time = datetime.now() + timedelta(minutes=5)

        # Store OTP in session
        request.session['deletion_otp'] = otp
        request.session['deletion_email'] = email
        request.session['deletion_otp_expiration'] = expiration_time.isoformat()

        # Send email
        try:
            send_mail(
                "Account Deletion Confirmation",
                f"Your account deletion OTP is {otp}. This code will expire in 5 minutes.\n\n"
                f"If you did not request this, please change your password immediately.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return Response({
                "message": "Deletion OTP sent to your email"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "Failed to send OTP email"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

import logging
from django.db import transaction
logger = logging.getLogger(__name__)

class ConfirmAccountDeletionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                user = request.user
                otp = request.data.get("otp")

                stored_otp = request.session.get('deletion_otp')
                stored_email = request.session.get('deletion_email')
                otp_expiration = request.session.get('deletion_otp_expiration')

                # Validate OTP
                if not otp:
                    return Response({
                        "error": "OTP is required"
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check expiration
                if not otp_expiration or datetime.fromisoformat(otp_expiration) < datetime.now():
                    return Response({
                        "error": "OTP has expired. Please request a new one."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Verify OTP
                if not secrets.compare_digest(stored_otp, otp) or not secrets.compare_digest(stored_email, user.email):
                    return Response({
                        "error": "Invalid OTP"
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Delete user's messages
                    Message.objects.filter(Q(sender=user) | Q(receiver=user)).delete()

                    # Delete user's chat group memberships
                    user.chat_groups.clear()

                    # Delete user's friendships
                    Friendship.objects.filter(Q(sender=user) | Q(receiver=user)).delete()

                    # Delete user's blocks
                    UserBlock.objects.filter(Q(blocker=user) | Q(blocked=user)).delete()

                    # Delete user's reports
                    UserReport.objects.filter(Q(reporter=user) | Q(reported_user=user)).delete()

                    # Delete profile
                    if hasattr(user, 'profile'):
                        profile = user.profile
                        if profile:
                            # Delete profile picture if exists
                            if profile.profile_picture:
                                profile.profile_picture.delete(save=False)
                            # Delete verification document if exists
                            if profile.verification_document:
                                profile.verification_document.delete(save=False)
                            profile.delete()

                    # Delete the user
                    user.delete()

                    # Clear session
                    request.session.flush()

                    return Response({
                        "message": "Account successfully deleted"
                    }, status=status.HTTP_200_OK)

                except Exception as e:
                    logger.error(f"Error during account deletion for user {user.username}: {str(e)}", exc_info=True)
                    raise

        except Exception as e:
            logger.error(f"Account deletion failed: {str(e)}", exc_info=True)
            return Response({
                "error": "Failed to delete account",
                "detail": str(e) if settings.DEBUG else "An unexpected error occurred"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.contrib.auth import authenticate
class VerifyPasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        user = authenticate(username=request.user.username, password=current_password)

        if user is not None:
            return Response({'message': 'Password verified'})
        return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordRequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]  # Changed to AllowAny

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Generate OTP
            otp = get_random_string(length=6, allowed_chars='0123456789')
            expiration_time = datetime.now() + timedelta(minutes=5)

            # Store OTP in session with email as key
            request.session[f'password_change_otp_{email}'] = otp
            request.session[f'password_change_otp_expiry_{email}'] = expiration_time.isoformat()

            # Send OTP via email
            send_mail(
                'Password Change Request',
                f'Your OTP for password change is: {otp}. Valid for 5 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return Response({'message': 'OTP sent successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordVerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]  # Changed to AllowAny

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = request.session.get(f'password_change_otp_{email}')
        expiry_time = request.session.get(f'password_change_otp_expiry_{email}')

        if not stored_otp or not expiry_time:
            return Response({'error': 'No OTP request found for this email'}, status=status.HTTP_400_BAD_REQUEST)

        if datetime.now() > datetime.fromisoformat(expiry_time):
            return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

        if otp != stored_otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP verified successfully'})

class ChangePasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]  # Changed to AllowAny

    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        otp = request.data.get('otp')
        
        if not email or not new_password or not otp:
            return Response({'error': 'Email, new password and OTP are required'}, 
                           status=status.HTTP_400_BAD_REQUEST)

        stored_otp = request.session.get(f'password_change_otp_{email}')

        if not stored_otp or otp != stored_otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # Clear the OTP from session
            del request.session[f'password_change_otp_{email}']
            del request.session[f'password_change_otp_expiry_{email}']

            return Response({'message': 'Password changed successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class UserBlockListCreateView(generics.ListCreateAPIView):
    """List all users blocked by the current user or block a new user"""
    serializer_class = UserBlockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBlock.objects.filter(blocker=self.request.user)

    def perform_create(self, serializer):
        blocked_user_id = self.request.data.get('blocked')
        if blocked_user_id:
            try:
                blocked_user = User.objects.get(id=blocked_user_id)
                serializer.save(blocker=self.request.user, blocked=blocked_user)
            except User.DoesNotExist:
                raise ValidationError(f"User with id {blocked_user_id} does not exist")
        else:
            raise ValidationError("'blocked' field is required")

class UserBlockDeleteView(generics.DestroyAPIView):
    """Unblock a previously blocked user"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBlock.objects.filter(blocker=self.request.user)

class ReportCategoryListView(generics.ListAPIView):
    """List all available report categories"""
    queryset = ReportCategory.objects.all()
    serializer_class = ReportCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class UserReportCreateView(generics.CreateAPIView):
    """Create a new user report"""
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        report = serializer.save(reporter=self.request.user)

        # Notify admins about the new report
        subject = f"New User Report: {report.reporter.username} reported {report.reported_user.username}"
        message = f"""
        A new user report has been filed:

        Reporter: {report.reporter.username} ({report.reporter.email})
        Reported User: {report.reported_user.username} ({report.reported_user.email})
        Category: {report.category.name}
        Description: {report.description}

        Please review this report at the admin dashboard.
        """
        # Send email to admins
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(admin_emails),
            fail_silently=True
        )

class UserReportListView(generics.ListAPIView):
    """List reports submitted by the current user"""
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserReport.objects.filter(reporter=self.request.user)

class FriendshipViewSet(viewsets.ModelViewSet):
    serializer_class = FriendshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Friendship.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender__profile', 'receiver__profile')

    def perform_create(self, serializer):
        receiver = serializer.validated_data['receiver']
        if receiver == self.request.user:
            raise ValidationError("You cannot send a friend request to yourself")

        if Friendship.objects.filter(sender=self.request.user, receiver=receiver).exists():
            raise ValidationError("Friend request already sent")

        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['POST'])
    def accept(self, request, pk=None):
        friendship = self.get_object()
        if friendship.receiver != request.user:
            return Response(
                {"error": "You can only accept requests sent to you"},
                status=status.HTTP_403_FORBIDDEN
            )

        friendship.status = 'accepted'
        friendship.save()

        # Return updated friendship status
        serializer = self.get_serializer(friendship)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk=None):
        friendship = self.get_object()
        if friendship.receiver != request.user:
            return Response(
                {"error": "You can only reject requests sent to you"},
                status=status.HTTP_403_FORBIDDEN
            )

        friendship.status = 'rejected'
        friendship.save()
        return Response({"status": "rejected"})

class UserReportDetailView(generics.RetrieveAPIView):
    """Allow users to view details of their own reports"""
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        report_id = self.kwargs.get('pk')
        report = get_object_or_404(UserReport, id=report_id, reporter=self.request.user)
        return report
    
# views.py (only for forgot password flow)
from django.core.cache import cache
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from rest_framework.throttling import AnonRateThrottle  # <-- Add this import

import secrets
from datetime import datetime, timedelta

User = get_user_model()

class ForgotPasswordSendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'forgot_password'

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "No user with this email exists"}, status=status.HTTP_404_NOT_FOUND)

        # Generate OTP (6-digit code)
        otp = get_random_string(length=6, allowed_chars='0123456789')
        expiry_time = datetime.now() + timedelta(minutes=5)  # OTP expires in 5 mins

        # Store in cache (better than session for APIs)
        cache_key = f"forgot_password_otp_{email}"
        cache.set(cache_key, {
            "otp": otp,
            "expiry": expiry_time.isoformat()
        }, timeout=300)  # Auto-delete after 5 mins

        # Send email (configure Django email backend!)
        send_mail(
            'Password Reset OTP',
            f'Your OTP is: {otp} (valid for 5 minutes)',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({"message": "OTP sent successfully"})

class ForgotPasswordVerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp_attempt = request.data.get("otp")

        if not email or not otp_attempt:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve from cache
        cache_key = f"forgot_password_otp_{email}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            return Response({"error": "OTP expired or invalid"}, status=status.HTTP_400_BAD_REQUEST)

        # Check expiry
        expiry_time = datetime.fromisoformat(cached_data["expiry"])
        if datetime.now() > expiry_time:
            cache.delete(cache_key)  # Clean up
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Secure OTP comparison
        if not secrets.compare_digest(otp_attempt, cached_data["otp"]):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a password reset token (one-time use)
        reset_token = get_random_string(50)
        cache.set(f"password_reset_token_{email}", reset_token, timeout=600)  # 10 mins

        return Response({
            "message": "OTP verified",
            "reset_token": reset_token  # Frontend sends this back in the next step
        })

class ForgotPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        reset_token = request.data.get("reset_token")
        new_password = request.data.get("new_password")

        if not all([email, reset_token, new_password]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the reset token
        cached_token = cache.get(f"password_reset_token_{email}")
        if not cached_token or cached_token != reset_token:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        # Update password
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # Cleanup cache
            cache.delete_many([
                f"password_reset_token_{email}",
                f"forgot_password_otp_{email}"
            ])

            return Response({"message": "Password reset successful"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)