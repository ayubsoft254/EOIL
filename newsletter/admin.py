from django.contrib import admin
from django.core.mail import EmailMessage, get_connection
from django.utils import timezone

from .models import NewsletterIssue, Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'subscribed_at')
    list_filter = ('is_active',)
    search_fields = ('email', 'name')


@admin.register(NewsletterIssue)
class NewsletterIssueAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'sent_at', 'sent_count')
    readonly_fields = ('sent_at', 'sent_count')
    actions = ['send_issue']

    @admin.action(description='Send selected issue(s) to active subscribers')
    def send_issue(self, request, queryset):
        subscribers = Subscriber.objects.filter(is_active=True)
        if not subscribers.exists():
            self.message_user(request, 'No active subscribers to send to.', level='warning')
            return
        connection = get_connection()
        for issue in queryset:
            if issue.is_sent:
                self.message_user(request, f'"{issue.subject}" was already sent — skipped.',
                                  level='warning')
                continue
            messages = []
            for sub in subscribers:
                footer = (f'\n\n—\nYou are receiving this because you subscribed to the '
                          f'EOIL TTU newsletter.\nUnsubscribe: '
                          f'{request.build_absolute_uri(f"/newsletter/unsubscribe/{sub.token}/")}')
                messages.append(EmailMessage(
                    subject=issue.subject,
                    body=issue.body + footer,
                    to=[sub.email],
                    connection=connection,
                ))
            connection.send_messages(messages)
            issue.sent_at = timezone.now()
            issue.sent_count = len(messages)
            issue.save(update_fields=['sent_at', 'sent_count'])
            self.message_user(request, f'"{issue.subject}" sent to {len(messages)} subscriber(s).')
