# myproject/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth.decorators import login_required
from django.conf import settings

from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView          # Deprecated cause created CustomViews
from myapp.views import TryLoginDumbWitView, LogoutView, CustomTokenRefreshView
from utils.media import secure_media_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('api/token/', TryLoginDumbWitView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/payments/', include('payments.urls')),
    path('api/', include('myapp.urls')),  # Remove cors_allow_registration wrapper
    re_path(
    r'^media/(?P<path>.*)$', 
        secure_media_serve,
        {'document_root': settings.MEDIA_ROOT}
    ),
]
