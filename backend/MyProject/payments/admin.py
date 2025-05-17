from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'status', 'processed_at')  # Changed created_at → processed_at
    search_fields = ('transaction_id', 'user__username')
    list_filter = ('status', 'currency')
    readonly_fields = ('processed_at',)  # Make timestamp non-editable
    list_per_page = 20

    exclude = ('raw_request',)

# from django.contrib import admin
# from django.utils.html import format_html
# from django.contrib.auth import get_user_model
# from .models import Payment

# User = get_user_model()

# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     # List view configuration
#     list_display = (
#         'transaction_id',
#         'user_email',
#         'amount_with_currency',
#         'status_badge',
#         'masked_card',
#         'partial_expiry',
#         'processed_at_short',
#     )
#     list_select_related = ('user',)
#     list_filter = (
#         'status',
#         'currency',
#         ('processed_at', admin.DateFieldListFilter),
#     )
#     search_fields = (
#         'transaction_id',
#         'user__email',
#         'user__username',
#         'card_last4',
#     )
#     list_per_page = 20
#     ordering = ('-processed_at',)
#     actions = ['export_as_json']

#     # Detail view configuration
#     fieldsets = (
#         ('Payment Information', {
#             'fields': (
#                 'transaction_id',
#                 'user_email_link',
#                 'amount_with_currency',
#                 'status_badge',
#                 'processed_at_short',
#             )
#         }),
#         ('Card Details (Masked)', {
#             'fields': (
#                 'masked_card',
#                 'partial_expiry',
#             ),
#             'classes': ('collapse',),
#         }),
#         ('Additional Information', {
#             'fields': (
#                 'ip_address',
#                 'secure_raw_data_preview',
#             ),
#             'classes': ('collapse',),
#         }),
#     )

#     readonly_fields = (
#         'transaction_id',
#         'user_email_link',
#         'amount_with_currency',
#         'status_badge',
#         'masked_card',
#         'partial_expiry',
#         'processed_at_short',
#         'secure_raw_data_preview',
#     )

#     # Custom methods for display
#     def user_email(self, obj):
#         return obj.user.email
#     user_email.short_description = 'User Email'
#     user_email.admin_order_field = 'user__email'

#     def user_email_link(self, obj):
#         return format_html(
#             '<a href="{}">{}</a>',
#             f'/admin/auth/user/{obj.user.id}/change/',
#             obj.user.email
#         )
#     user_email_link.short_description = 'User'

#     def amount_with_currency(self, obj):
#         return f"{obj.amount} {obj.currency}"
#     amount_with_currency.short_description = 'Amount'

#     def status_badge(self, obj):
#         color = {
#             'success': 'green',
#             'failed': 'red',
#             'pending': 'orange',
#         }.get(obj.status, 'gray')
#         return format_html(
#             '<span style="color: white; background-color: {};'
#             'padding: 3px 8px; border-radius: 4px;">{}</span>',
#             color,
#             obj.get_status_display().upper()
#         )
#     status_badge.short_description = 'Status'
#     status_badge.admin_order_field = 'status'

#     def processed_at_short(self, obj):
#         return obj.processed_at.strftime("%Y-%m-%d %H:%M")
#     processed_at_short.short_description = 'Processed At'
#     processed_at_short.admin_order_field = 'processed_at'

#     def secure_raw_data_preview(self, obj):
#         if not obj.raw_request:
#             return "No raw data available"
        
#         from django.contrib.auth.models import Permission
#         if not self.has_decrypt_permission(self.request):
#             return format_html(
#                 "<div style='color: red;'>"
#                 "⚠️ Sensitive data hidden - requires 'payments.view_sensitive_payment' permission"
#                 "</div>"
#             )
        
#         try:
#             decrypted = obj.decrypted_request
#             return format_html(
#                 "<div style='max-height: 300px; overflow: auto;'>"
#                 "<pre style='white-space: pre-wrap;'>{}</pre>"
#                 "</div>",
#                 str(decrypted)
#             )
#         except Exception as e:
#             return format_html(
#                 "<div style='color: red;'>"
#                 "⚠️ Decryption failed: {}"
#                 "</div>",
#                 str(e)
#             )
#     secure_raw_data_preview.short_description = 'Raw Data (Secure)'

#     # Security methods
#     def get_queryset(self, request):
#         self.request = request
#         qs = super().get_queryset(request)
#         if not self.has_decrypt_permission(request):
#             qs = qs.defer('raw_request')
#         return qs

#     def has_decrypt_permission(self, request):
#         return request.user.has_perm('payments.view_sensitive_payment')

#     # Custom admin actions
#     def export_as_json(self, request, queryset):
#         import json
#         from django.http import HttpResponse
#         from django.core.serializers.json import DjangoJSONEncoder

#         data = []
#         for payment in queryset:
#             data.append({
#                 'transaction_id': payment.transaction_id,
#                 'amount': str(payment.amount),
#                 'currency': payment.currency,
#                 'status': payment.status,
#                 'processed_at': payment.processed_at.isoformat(),
#                 'card_last4': payment.card_last4,
#             })

#         response = HttpResponse(
#             json.dumps(data, indent=2, cls=DjangoJSONEncoder),
#             content_type='application/json'
#         )
#         response['Content-Disposition'] = 'attachment; filename=payments_export.json'
#         return response
#     export_as_json.short_description = "Export selected payments as JSON"

#     # Change list customization
#     def changelist_view(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         extra_context['show_decrypt_warning'] = not self.has_decrypt_permission(request)
#         return super().changelist_view(request, extra_context=extra_context)

#     # Form customization
#     def get_fieldsets(self, request, obj=None):
#         fieldsets = super().get_fieldsets(request, obj)
#         if self.has_decrypt_permission(request):
#             fieldsets += (
#                 ('Sensitive Data (Decrypted)', {
#                     'fields': ('secure_raw_data_preview',),
#                     'classes': ('collapse',),
#                     'description': '⚠️ Requires special permissions'
#                 }),
#             )
#         return fieldsets