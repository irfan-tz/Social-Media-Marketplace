from django.db.models import Q  
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .models import Message, Profile
from .serializers import MessageSerializer, UserRegistrationSerializer, UserSerializer
from rest_framework.parsers import MultiPartParser, FormParser


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
        serializer.save(sender=self.request.user)

class MessageDetailView(generics.RetrieveAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]





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
        
        if chat_group_id:
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


