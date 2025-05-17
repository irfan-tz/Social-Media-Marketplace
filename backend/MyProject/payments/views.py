from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import random
import logging
from django.conf import settings
from django.utils import timezone
from .models import Payment
from django.contrib.auth import get_user_model
import copy  # Needed for deep copy of request data

logger = logging.getLogger(__name__)
User = get_user_model()

class SimulatePaymentView(APIView):
    """
    Processes simulated payments and logs them to database
    Required POST data:
    - card_number: string (15-16 digits)
    - expiry: string (MMYY format)
    - cvv: string (3-4 digits)
    - amount: number
    
    Sensitive data (CVV, full card number, expiry) are masked before storage
    """
    
    def post(self, request):
        # ======================
        # 1. DATA VALIDATION
        # ======================
        try:
            # Extract and clean data
            card_number = request.data.get('card_number', '').replace(' ', '')
            expiry = request.data.get('expiry', '').replace('/', '')
            cvv = request.data.get('cvv', '')
            
            # Validate amount
            try:
                amount = Decimal(str(request.data.get('amount', 0)))
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except (TypeError, ValueError) as e:
                logger.warning(f"Invalid amount: {request.data.get('amount')}")
                return Response(
                    {'error': 'Invalid amount - must be a positive number'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate required fields
            if not all([card_number, expiry, cvv]):
                missing = [f for f in ['card_number', 'expiry', 'cvv'] if not request.data.get(f)]
                logger.warning(f"Missing fields: {missing}")
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate card number
            if not card_number.isdigit() or len(card_number) not in (15, 16):
                logger.warning(f"Invalid card number: {card_number}")
                return Response(
                    {'error': 'Invalid card number - must be 15 or 16 digits'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate expiry
            if not expiry.isdigit() or len(expiry) != 4:
                logger.warning(f"Invalid expiry: {expiry}")
                return Response(
                    {'error': 'Invalid expiry date - must be MMYY format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate CVV
            if not cvv.isdigit() or len(cvv) not in (3, 4):
                logger.warning(f"Invalid CVV: {cvv}")
                return Response(
                    {'error': 'Invalid CVV - must be 3 or 4 digits'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ======================
            # 2. PAYMENT PROCESSING
            # ======================
            logger.info(f"Processing payment for user {request.user.id}: {card_number[-4:]} {amount}{settings.SIMULATED_PAYMENT.get('CURRENCY', 'INR')}")
            
            # Simulate payment with success rate
            success = random.random() < settings.SIMULATED_PAYMENT.get('SUCCESS_RATE', 1.0)
            transaction_id = f"{'TXN' if success else 'FAIL'}{random.randint(100000, 999999)}"

            # ======================
            # 3. DATABASE LOGGING (WITH DATA MASKING)
            # ======================
            # Create sanitized version of request data
            sanitized_data = copy.deepcopy(request.data)
            
            # Mask sensitive fields
            sanitized_data['cvv'] = '***'  # Always mask CVV
            sanitized_data['card_number'] = f"**** **** **** {card_number[-4:]}"  # Mask card number
            sanitized_data['expiry'] = '****'  # Mask expiry date
            
            payment = Payment.objects.create(
                user=request.user,
                transaction_id=transaction_id,
                amount=amount,
                currency=settings.SIMULATED_PAYMENT.get('CURRENCY', 'INR'),
                card_last4=card_number[-4:],
                status='success' if success else 'failed',
                raw_request=sanitized_data,  # Use sanitized data instead of original
                processed_at=timezone.now()
            )

            # ======================
            # 4. RESPONSE
            # ======================
            if success:
                logger.info(f"Payment succeeded: {transaction_id}")
                return Response({
                    'status': 'success',
                    'transaction_id': transaction_id,
                    'amount': str(amount),
                    'currency': payment.currency,
                    'masked_card': f"**** **** **** {payment.card_last4}",
                    'timestamp': payment.processed_at.isoformat()
                }, status=status.HTTP_200_OK)
            
            logger.warning(f"Payment failed: {transaction_id}")
            return Response({
                'status': 'failed',
                'transaction_id': transaction_id,
                'reason': 'Payment declined by bank',
                'code': 'DECLINED',
                'timestamp': payment.processed_at.isoformat()
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Internal server error',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )