from django.contrib import admin
from .models import (
    Profile, ChatGroup, Message, ChatGroupMessage,
    UserBlock, ReportCategory, UserReport, AdminAction, Friendship
)
from django.utils.html import format_html
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('sender__username', 'receiver__username')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_username', 'get_profile_picture_status','is_verified', 'verification_submitted_at')
    list_filter = ('is_verified', 'verification_submitted_at')
    list_editable = ('is_verified',)
    actions = ['verify_profiles', 'unverify_profiles']
    search_fields = ('user__username',)
    raw_id_fields = ('user',)

    def get_username(self, obj):
        """
        Return the username of the associated user.
        """
        return obj.user.username
    get_username.short_description = 'Username'

    def get_profile_picture_status(self, obj):
        """
        Return whether a profile picture is uploaded.
        """
        return 'Uploaded' if obj.profile_picture else 'Not Set'
    get_profile_picture_status.short_description = 'Profile Picture'

    def verify_profiles(self, request, queryset):
        queryset.update(is_verified=True)
    verify_profiles.short_description = "Verify selected profiles"

    def unverify_profiles(self, request, queryset):
        queryset.update(is_verified=False)
    unverify_profiles.short_description = "Unverify selected profiles"

    readonly_fields = ('verification_document_preview',)

    def verification_document_preview(self, obj):
        if obj.verification_document:
            return format_html(
                '<a href="{}" target="_blank">View Document</a>',
                obj.verification_document.url
            )
        return "-"
    verification_document_preview.short_description = "Verification Document"

from django.http import HttpResponseRedirect
from django.contrib import messages

# Register basic models with minimal customization
@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('blocker__username', 'blocked__username')
    readonly_fields = ('created_at',)

@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

# Custom admin action to ban user and send notification
def ban_user(modeladmin, request, queryset):
    # Only allow action on one report at a time
    if queryset.count() != 1:
        messages.error(request, "Please select exactly one report to take action on.")
        return

    report = queryset.first()
    user_to_ban = report.reported_user

    # Create admin action record
    admin_action = AdminAction.objects.create(
        report=report,
        admin=request.user,
        action='perm_ban',
        notes=f"User {user_to_ban.username} was permanently banned by admin {request.user.username}"
    )

    # Update report status
    report.status = 'action_taken'
    report.admin_notes += f"\n[{admin_action.created_at.strftime('%Y-%m-%d %H:%M')}] User permanently banned."
    report.save()

    # Send notification email
    try:
        send_mail(
            subject="Your account has been deleted",
            message=f"""
Dear {user_to_ban.username},

Your account has been deleted due to community reports and violations
of our terms of service.

If you believe this is an error, you may contact our support team.

Regards,
The Admin Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_to_ban.email],
            fail_silently=True
        )
    except Exception as e:
        messages.warning(request, f"Email notification failed: {str(e)}")

    # Delete the user
    user_to_ban.delete()

    messages.success(request, f"User {user_to_ban.username} has been banned and their account deleted.")

ban_user.short_description = "Ban user and delete their account"

# Custom admin action to mark as reviewed with no action
def mark_reviewed(modeladmin, request, queryset):
    for report in queryset:
        AdminAction.objects.create(
            report=report,
            admin=request.user,
            action='reviewed',
            notes=f"Report reviewed by admin {request.user.username}, no action required."
        )
        report.status = 'resolved'
        report.admin_notes += f"\n[{AdminAction.objects.filter(report=report).latest('created_at').created_at.strftime('%Y-%m-%d %H:%M')}] Report reviewed, no action taken."
        report.save()

    messages.success(request, f"{queryset.count()} report(s) marked as reviewed with no action required.")

mark_reviewed.short_description = "Mark as reviewed (no action)"

# Custom UserReport admin
@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'reported_user', 'category', 'status', 'created_at', 'has_evidence', 'admin_actions', 'ban_actions')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('reporter__username', 'reported_user__username', 'description')
    readonly_fields = ('reporter', 'reported_user', 'category', 'description', 'evidence', 'created_at', 'admin_actions_detail', 'ban_user_button')
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'reported_user', 'category', 'description')
        }),
        ('Evidence', {
            'fields': ('evidence',)
        }),
        ('Status', {
            'fields': ('status', 'admin_notes')
        }),
        ('Actions', {
            'fields': ('ban_user_button', 'admin_actions_detail',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    actions = [mark_reviewed, ban_user]

    def has_evidence(self, obj):
        return bool(obj.evidence)
    has_evidence.boolean = True
    has_evidence.short_description = "Evidence"

    def admin_actions(self, obj):
        actions = obj.admin_actions.all()
        count = actions.count()
        if count == 0:
            return "No actions"

        latest = actions.latest('created_at')
        return format_html('<span title="{}">Latest: {}</span>',
                           latest.notes,
                           latest.get_action_display())
    admin_actions.short_description = "Admin Actions"

    def ban_actions(self, obj):
        """Add direct ban button on list view"""
        url = reverse('admin:myapp_userreport_ban', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="background-color: #d9534f; color: white; padding: 5px 10px; border-radius: 4px;">'
            '<i class="fas fa-ban"></i> Ban User</a>',
            url
        )
    ban_actions.short_description = "Ban User"

    def ban_user_button(self, obj):
        """Add prominent ban button in detail view"""
        url = reverse('admin:myapp_userreport_ban', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" '
            'style="background-color: #d9534f; color: white; padding: 10px 20px; '
            'border-radius: 4px; font-weight: bold; display: inline-block; margin-top: 10px; '
            'text-align: center;">'
            '<i class="fas fa-ban"></i> Ban User {}</a>',
            url, obj.reported_user.username
        )
    ban_user_button.short_description = "Actions"

    def admin_actions_detail(self, obj):
        actions = obj.admin_actions.all().order_by('-created_at')
        if not actions:
            return "No admin actions recorded."

        html = '<ul>'
        for action in actions:
            html += f'<li><strong>{action.created_at.strftime("%Y-%m-%d %H:%M")}</strong> - <em>{action.get_action_display()}</em> by {action.admin.username}<br>{action.notes}</li>'
        html += '</ul>'
        return format_html(html)
    admin_actions_detail.short_description = "Admin Actions History"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/ban/', self.admin_site.admin_view(self.ban_user_view), name='myapp_userreport_ban'),
        ]
        return custom_urls + urls

    def ban_user_view(self, request, object_id, *args, **kwargs):
        """Handle the ban user action"""
        report = self.get_queryset(request).get(pk=object_id)
        user_to_ban = report.reported_user

        # Create admin action record
        admin_action = AdminAction.objects.create(
            report=report,
            admin=request.user,
            action='perm_ban',
            notes=f"User {user_to_ban.username} was permanently banned by admin {request.user.username}"
        )

        # Update report status
        report.status = 'action_taken'
        report.admin_notes += f"\n[{admin_action.created_at.strftime('%Y-%m-%d %H:%M')}] User permanently banned."
        report.save()

        # Send notification email
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            send_mail(
                subject="Your account has been deleted",
                message=f"""
Dear {user_to_ban.username},

Your account has been deleted due to community reports and violations
of our terms of service.

If you believe this is an error, you may contact our support team.

Regards,
The Admin Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_to_ban.email],
                fail_silently=True
            )
        except Exception as e:
            self.message_user(request, f"Email notification failed: {str(e)}", level=messages.WARNING)

        # Delete the user
        username = user_to_ban.username  # Store for message
        user_to_ban.delete()

        self.message_user(request, f"User {username} has been banned and their account deleted.")
        return redirect('admin:myapp_userreport_changelist')

    def save_model(self, request, obj, form, change):
        """Send notifications when report status changes"""
        if change and 'status' in form.changed_data:
            old_status = UserReport.objects.get(pk=obj.pk).status
            new_status = obj.status

            # Send email notification to reporter about status change
            try:
                from django.core.mail import send_mail
                from django.conf import settings

                status_messages = {
                    'pending': "Your report is pending review.",
                    'reviewing': "Your report is now being reviewed by our moderation team.",
                    'resolved': "Your report has been resolved. No further action was deemed necessary.",
                    'action_taken': "Your report has been resolved. We've taken appropriate action."
                }

                send_mail(
                    subject=f"Update on your report against {obj.reported_user.username}",
                    message=f"""
    Dear {obj.reporter.username},

    The status of your report against {obj.reported_user.username} has been updated to: {obj.get_status_display()}.

    {status_messages.get(obj.status, "")}

    Thank you for helping keep our community safe.

    Regards,
    The Moderation Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[obj.reporter.email],
                    fail_silently=True
                )
            except Exception as e:
                self.message_user(request, f"Failed to send status update email: {str(e)}", level=messages.WARNING)

        super().save_model(request, obj, form, change)

@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    list_display = ('report_link', 'admin', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('report__reporter__username', 'report__reported_user__username', 'admin__username', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('report', 'admin', 'action', 'created_at')

    def has_add_permission(self, request):
        return False

    def report_link(self, obj):
        return format_html('<a href="{}">{}</a>',
                           f'/admin/myapp/userreport/{obj.report.id}/change/',
                           f'Report #{obj.report.id}')
    report_link.short_description = "Report"

# Register other models
@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name', 'created_by__username')
    filter_horizontal = ('members',)

@admin.register(ChatGroupMessage)
class ChatGroupMessageAdmin(admin.ModelAdmin):
    list_display = ('chat_group', 'sender', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('chat_group__name', 'sender__username')

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__username', 'receiver__username')
