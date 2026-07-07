import csv
import io
from urllib.parse import urlencode

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegistrationForm
from .models import Event, Registration
from .pdf import build_ticket_pdf


def event_list(request):
    now = timezone.now()
    published = Event.objects.filter(is_published=True)
    upcoming = published.filter(end_at__gte=now).order_by('start_at')
    past = published.filter(end_at__lt=now).order_by('-start_at')
    return render(request, 'events/list.html', {'upcoming': upcoming, 'past': past})


def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    form = RegistrationForm()

    if request.method == 'POST':
        if not event.registration_open:
            messages.error(request, 'Registration for this event has closed.')
            return redirect(event.get_absolute_url())
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            if event.registrations.filter(email__iexact=email).exclude(
                    status=Registration.Status.CANCELLED).exists():
                messages.error(
                    request,
                    'This email address is already registered for this event. '
                    'Check your confirmation email for your ticket link.')
            else:
                registration = form.save(commit=False)
                registration.event = event
                registration.email = email
                if event.is_full:
                    registration.status = Registration.Status.WAITLISTED
                registration.save()
                _send_confirmation_email(request, registration)
                return redirect('events:ticket', ticket_code=registration.ticket_code)

    return render(request, 'events/detail.html', {'event': event, 'form': form})


def _send_confirmation_email(request, registration):
    event = registration.event
    ticket_url = request.build_absolute_uri(f'/events/ticket/{registration.ticket_code}/')
    if registration.status == Registration.Status.WAITLISTED:
        status_line = ('The event is currently at capacity, so you have been added to the '
                       'waitlist. We will notify you if a spot opens up.')
    else:
        status_line = 'Your spot is confirmed. Present your ticket at the check-in desk.'
    send_mail(
        subject=f'Registration received — {event.title}',
        message=(
            f'Hello {registration.full_name},\n\n'
            f'Thank you for registering for {event.title} '
            f'({event.start_at.strftime("%d %b %Y, %H:%M")} at {event.venue}).\n\n'
            f'{status_line}\n\n'
            f'Ticket code: {registration.ticket_code}\n'
            f'Ticket link: {ticket_url}\n'
            f'PDF ticket: {ticket_url}pdf/\n\n'
            f'— EOIL @ Taita Taveta University'
        ),
        from_email=None,
        recipient_list=[registration.email],
        fail_silently=True,
    )


def ticket(request, ticket_code):
    registration = get_object_or_404(Registration, ticket_code=ticket_code)
    qr_svg = _qr_svg(registration.ticket_code)
    return render(request, 'events/ticket.html',
                  {'registration': registration, 'event': registration.event, 'qr_svg': qr_svg})


def ticket_pdf(request, ticket_code):
    registration = get_object_or_404(Registration, ticket_code=ticket_code)
    pdf_bytes = build_ticket_pdf(registration)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket-{registration.ticket_code}.pdf"'
    return response


def _qr_svg(data):
    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, box_size=14)
    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue().decode()


# --- Staff check-in ---------------------------------------------------------

@staff_member_required
def checkin_home(request):
    events = Event.objects.filter(is_published=True).order_by('-start_at')
    return render(request, 'events/checkin_home.html', {'events': events})


@staff_member_required
def checkin_dashboard(request, slug):
    event = get_object_or_404(Event, slug=slug)
    registrations = event.registrations.exclude(status=Registration.Status.CANCELLED)
    query = request.GET.get('q', '').strip()
    if query:
        registrations = registrations.filter(
            Q(full_name__icontains=query) | Q(email__icontains=query) |
            Q(ticket_code__icontains=query) | Q(organization__icontains=query))
    return render(request, 'events/checkin_dashboard.html', {
        'event': event,
        'registrations': registrations.order_by('full_name'),
        'query': query,
        'waitlisted_count': event.registrations.filter(
            status=Registration.Status.WAITLISTED).count(),
    })


@staff_member_required
@require_POST
def checkin_by_code(request, slug):
    """Quick check-in from the ticket-code box (or a QR scanner acting as a keyboard)."""
    event = get_object_or_404(Event, slug=slug)
    code = request.POST.get('ticket_code', '').strip().upper()
    try:
        registration = event.registrations.get(ticket_code=code)
    except Registration.DoesNotExist:
        messages.error(request, f'No ticket "{code}" found for this event.')
        return redirect('events:checkin', slug=slug)
    if registration.status == Registration.Status.CANCELLED:
        messages.error(request, f'{registration.full_name} — registration was cancelled.')
    elif registration.checked_in:
        messages.warning(
            request,
            f'{registration.full_name} was already checked in at '
            f'{timezone.localtime(registration.checked_in_at).strftime("%H:%M")}.')
    else:
        registration.check_in()
        messages.success(request, f'{registration.full_name} checked in. Welcome!')
    return redirect('events:checkin', slug=slug)


@staff_member_required
@require_POST
def checkin_toggle(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    registration = get_object_or_404(Registration, pk=pk, event=event)
    if registration.checked_in:
        registration.undo_check_in()
        messages.info(request, f'Check-in undone for {registration.full_name}.')
    else:
        registration.check_in()
        messages.success(request, f'{registration.full_name} checked in.')
    url = reverse('events:checkin', args=[slug])
    query = request.POST.get('q', '')
    if query:
        url += '?' + urlencode({'q': query})
    return redirect(url)


@staff_member_required
def export_registrations_csv(request, slug):
    event = get_object_or_404(Event, slug=slug)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.slug}-participants.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Organization', 'Category',
                     'Status', 'Ticket code', 'Checked in', 'Checked in at', 'Registered at'])
    for reg in event.registrations.exclude(status=Registration.Status.CANCELLED):
        writer.writerow([
            reg.full_name, reg.email, reg.phone, reg.organization,
            reg.get_category_display(), reg.get_status_display(), reg.ticket_code,
            'Yes' if reg.checked_in else 'No',
            timezone.localtime(reg.checked_in_at).strftime('%Y-%m-%d %H:%M') if reg.checked_in_at else '',
            timezone.localtime(reg.registered_at).strftime('%Y-%m-%d %H:%M'),
        ])
    return response
