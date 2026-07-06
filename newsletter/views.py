from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import SubscribeForm
from .models import Subscriber


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email'].lower()
        subscriber, created = Subscriber.objects.get_or_create(
            email=email, defaults={'name': form.cleaned_data.get('name', '')})
        if created:
            messages.success(request, 'You are subscribed! Watch your inbox for EOIL TTU updates.')
        elif not subscriber.is_active:
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
            messages.success(request, 'Welcome back — your subscription has been reactivated.')
        else:
            messages.info(request, 'This email is already subscribed to the newsletter.')
    else:
        messages.error(request, 'Please enter a valid email address.')
    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = '/'
    return redirect(next_url)


def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if subscriber.is_active:
        subscriber.is_active = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
    return render(request, 'newsletter/unsubscribed.html', {'subscriber': subscriber})
