from django.views.static import serve
from django.core.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
import os

def secure_media_serve(request, path, document_root=None, show_indexes=False):
    """
    Media serving view with selective access control for JWT authentication
    """
    # Resolve the absolute path to prevent directory traversal
    abs_document_root = os.path.abspath(document_root)
    abs_path = os.path.normpath(os.path.join(abs_document_root, path))
    
    # Ensure the requested file is within the document root
    if not abs_path.startswith(abs_document_root):
        raise PermissionDenied("Invalid file path")
    
    # Validate file type
    filename = os.path.basename(abs_path)
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise PermissionDenied("File type not allowed")
    
    # Special handling for profile pictures
    if 'profile_pics' in path:
        # Profile pictures are public
        return serve(request, path, document_root=document_root, show_indexes=False)
    
    # For all other media, require authentication
    access_token = request.COOKIES.get('access_token')
    
    if not access_token:
        raise PermissionDenied("Authentication required to access this media")
    
    try:
        # Validate the token
        validated_token = AccessToken(access_token)
        # Optional: You can add additional checks here if needed
    except (InvalidToken, TokenError):
        raise PermissionDenied("Invalid or expired token")
    
    # Optional: File size limit check
    max_file_size = 5 * 1024 * 1024  # 5 MB
    if os.path.exists(abs_path) and os.path.getsize(abs_path) > max_file_size:
        raise PermissionDenied("File size exceeds limit")
    
    # Serve the file
    return serve(request, path, document_root=document_root, show_indexes=False)