# payments/models.py
# from django.db import models
# from django.contrib.auth import get_user_model

# class Payment(models.Model):
#     user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
#     transaction_id = models.CharField(max_length=50, unique=True)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     currency = models.CharField(max_length=3, default='INR')
#     card_last4 = models.CharField(max_length=4)
#     status = models.CharField(max_length=20)  # success/failed
#     raw_request = models.JSONField(default=dict)  # Stores original request data
#     processed_at = models.DateTimeField(auto_now_add=True)  # This is what we're using
    
#     class Meta:
#         ordering = ['-processed_at']
#         verbose_name = 'Payment Record'
#         verbose_name_plural = 'Payment Records'

#     def __str__(self):
#         return f"{self.transaction_id} ({self.status})"

# payments/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class Payment(models.Model):
    """
    Payment record model with enhanced security features:
    - Automatically masks sensitive data in raw_request
    - Validates payment data integrity
    - Provides audit capabilities
    """
    
    # Status choices for better validation
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.PROTECT,
        related_name='payments'
    )
    transaction_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique transaction identifier from payment processor"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount charged in the specified currency"
    )
    currency = models.CharField(
        max_length=3,
        default='INR',
        help_text="ISO 4217 currency code"
    )
    card_last4 = models.CharField(
        max_length=4,
        help_text="Last 4 digits of the payment card"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Current status of the payment"
    )
    raw_request = models.JSONField(
        default=dict,
        help_text="Sanitized payment request data (sensitive fields are masked)"
    )
    processed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when payment was processed"
    )
    
    class Meta:
        ordering = ['-processed_at']
        verbose_name = 'Payment Record'
        verbose_name_plural = 'Payment Records'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', 'processed_at']),
        ]

    def __str__(self):
        return f"{self.transaction_id} ({self.status}) - {self.amount} {self.currency}"

    def clean(self):
        """
        Additional model-wide validation
        """
        super().clean()
        
        # Validate card_last4 contains exactly 4 digits
        if not (self.card_last4.isdigit() and len(self.card_last4) == 4):
            raise ValidationError({
                'card_last4': 'Must be exactly 4 digits'
            })
        
        # Validate currency is uppercase
        if not self.currency.isupper():
            self.currency = self.currency.upper()

    def save(self, *args, **kwargs):
        """
        Override save to:
        - Automatically sanitize sensitive data in raw_request
        - Add validation
        """
        self._sanitize_raw_request()
        self.full_clean()
        super().save(*args, **kwargs)

    def _sanitize_raw_request(self):
        """
        Ensure sensitive data is masked in raw_request before saving
        """
        if not isinstance(self.raw_request, dict):
            logger.warning(f"Invalid raw_request type: {type(self.raw_request)}")
            self.raw_request = {}
            return

        sensitive_fields = {
            'cvv': '***',
            'card_number': f"**** **** **** {self.card_last4}",
            'expiry': '****',
            'security_code': '***',
            'card_cvc': '***'
        }

        for field, mask in sensitive_fields.items():
            if field in self.raw_request:
                original_value = str(self.raw_request[field])
                if not original_value.startswith('****') and original_value != '***':
                    logger.info(
                        f"Masking sensitive field '{field}' in payment {self.transaction_id}"
                    )
                    self.raw_request[field] = mask

    @property
    def masked_card(self):
        """Helper property to display masked card number consistently"""
        return f"**** **** **** {self.card_last4}"

    @property
    def amount_display(self):
        """Formatted amount with currency symbol"""
        return f"{self.currency} {self.amount:.2f}"