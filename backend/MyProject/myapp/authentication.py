from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import exceptions

class CookiesJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # First try to get access token from cookies
        access_token = request.COOKIES.get('access_token')
        
        # If no access token, return None (which means no authentication)
        if not access_token:
            return None
        
        try:
            # Validate the token
            validated_token = self.get_validated_token(access_token)
            
            # Get the user
            try:
                user = self.get_user(validated_token)
            except AuthenticationFailed:
                # If user is not found or token is invalid
                return None
            
            return (user, validated_token)
        
        except Exception as e:
            # Log the specific authentication error if needed
            print(f"Authentication error: {e}")
            return None