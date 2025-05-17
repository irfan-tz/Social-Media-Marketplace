from django.urls import path, include
# from payment.views import CreateRazorpayOrder
from rest_framework.routers import DefaultRouter
from .views import FriendshipViewSet  # Import your viewset

router = DefaultRouter()
router.register(r'friendships', FriendshipViewSet, basename='friendship')

from .views import (
    # Existing views
    MessageListCreateView,
    MessageDetailView,
    UserCreateView,
    ProfileRetrieveView,
    ProfileUpdateView,
    UserListView,
    CurrentUserView,
    UserProfileView,

    ChatGroupListCreateView,
    ChatGroupDetailView,
    ChatGroupMessageListCreateView,
    ChatMessageListCreateView,
    ServeDecryptedFileView,
    SendOTPView,
    VerifyOTPView,

    RequestAccountDeletionView,
    ConfirmAccountDeletionView,

    VerifyPasswordView,
    ChangePasswordRequestOTPView,
    ChangePasswordVerifyOTPView,
    ChangePasswordResetView,

    UserBlockListCreateView,
    UserBlockDeleteView,
    ReportCategoryListView,
    UserReportCreateView,
    UserReportListView,
    UserReportDetailView,

    ForgotPasswordSendOTPView,
    ForgotPasswordVerifyOTPView, 
    ForgotPasswordResetView
)

urlpatterns = [
    # Message-related endpoints
    path('messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('messages/<int:message_id>/attachment/', ServeDecryptedFileView.as_view(), name='serve_decrypted_file'),

    path('chat_groups/', ChatGroupListCreateView.as_view(), name='chat-group-list-create'),
    path('chat_groups/<int:pk>/', ChatGroupDetailView.as_view(), name='chat-group-detail'),
    path('chat_groups/<int:chat_group_id>/messages/', ChatGroupMessageListCreateView.as_view(), name='chat-group-message-list-create'),
    path('chat_messages/', ChatMessageListCreateView.as_view(), name='chat-message-list-create'),

    # User-related endpoints
    path('register/', UserCreateView.as_view(), name='register'),
    path('profile/', ProfileRetrieveView.as_view(), name='profile-retrieve'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
    path('users/<str:username>/profile/', UserProfileView.as_view(), name='user-profile'),

    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    path('delete-account/request/', RequestAccountDeletionView.as_view(), name='request-account-deletion'),
    path('delete-account/confirm/', ConfirmAccountDeletionView.as_view(), name='confirm-account-deletion'),

    path('verify-password/', VerifyPasswordView.as_view(), name='verify-password'),
    path('change-password/request-otp/', ChangePasswordRequestOTPView.as_view(), name='change-password-request-otp'),
    path('change-password/verify-otp/', ChangePasswordVerifyOTPView.as_view(), name='change-password-verify-otp'),
    path('change-password/reset/', ChangePasswordResetView.as_view(), name='change-password-reset'),
    #path('create-order/', CreateRazorpayOrder.as_view(), name='create-order'),

    path('blocks/', UserBlockListCreateView.as_view(), name='user-block-list'),
    path('blocks/<int:pk>/', UserBlockDeleteView.as_view(), name='user-block-delete'),
    path('report-categories/', ReportCategoryListView.as_view(), name='report-category-list'),
    path('reports/', UserReportCreateView.as_view(), name='user-report-create'),
    path('my-reports/', UserReportListView.as_view(), name='user-report-list'),
    path('my-reports/<int:pk>/', UserReportDetailView.as_view(), name='user-report-detail'),
    path('api/forgot-password/send-otp/', ForgotPasswordSendOTPView.as_view()),
    path('api/forgot-password/verify-otp/', ForgotPasswordVerifyOTPView.as_view()),
    path('api/forgot-password/reset/', ForgotPasswordResetView.as_view()),
    path('', include(router.urls)),
]
