from django.shortcuts import render
from django.utils import timezone

from events.models import Event


def home(request):
    upcoming_events = (Event.objects
                       .filter(is_published=True, end_at__gte=timezone.now())
                       .order_by('start_at')[:3])
    return render(request, 'core/home.html', {'upcoming_events': upcoming_events})
