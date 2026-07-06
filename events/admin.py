import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone

from .models import Event, Registration


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    fields = ('full_name', 'email', 'category', 'status', 'ticket_code', 'checked_in')
    readonly_fields = ('ticket_code',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_at', 'venue', 'capacity',
                    'confirmed_count', 'checked_in_count', 'is_published')
    list_filter = ('event_type', 'is_published')
    search_fields = ('title', 'venue')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_at'
    inlines = [RegistrationInline]

    @admin.display(description='Confirmed')
    def confirmed_count(self, obj):
        return obj.confirmed_count

    @admin.display(description='Checked in')
    def checked_in_count(self, obj):
        return obj.checked_in_count


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'event', 'category', 'status',
                    'ticket_code', 'checked_in', 'registered_at')
    list_filter = ('event', 'status', 'category', 'checked_in')
    search_fields = ('full_name', 'email', 'ticket_code', 'organization')
    readonly_fields = ('ticket_code', 'registered_at', 'checked_in_at')
    actions = ['mark_checked_in', 'mark_not_checked_in', 'export_csv']

    @admin.action(description='Mark selected as checked in')
    def mark_checked_in(self, request, queryset):
        updated = queryset.filter(checked_in=False).update(
            checked_in=True, checked_in_at=timezone.now())
        self.message_user(request, f'{updated} participant(s) checked in.')

    @admin.action(description='Undo check-in for selected')
    def mark_not_checked_in(self, request, queryset):
        updated = queryset.filter(checked_in=True).update(
            checked_in=False, checked_in_at=None)
        self.message_user(request, f'Check-in undone for {updated} participant(s).')

    @admin.action(description='Export selected to CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="registrations.csv"'
        writer = csv.writer(response)
        writer.writerow(['Event', 'Name', 'Email', 'Phone', 'Organization',
                         'Category', 'Status', 'Ticket code', 'Checked in', 'Registered at'])
        for reg in queryset.select_related('event'):
            writer.writerow([reg.event.title, reg.full_name, reg.email, reg.phone,
                             reg.organization, reg.get_category_display(),
                             reg.get_status_display(), reg.ticket_code,
                             'Yes' if reg.checked_in else 'No',
                             reg.registered_at.strftime('%Y-%m-%d %H:%M')])
        return response
