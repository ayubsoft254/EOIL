import secrets

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


def generate_ticket_code():
    """Short, human-readable ticket code, e.g. TTU-7K2F9QAB."""
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # no 0/O/1/I
    code = ''.join(secrets.choice(alphabet) for _ in range(8))
    return f'TTU-{code}'


class Event(models.Model):
    class EventType(models.TextChoices):
        HACKATHON = 'hackathon', 'Hackathon'
        CONFERENCE = 'conference', 'Conference'
        WORKSHOP = 'workshop', 'Workshop'
        TRAINING = 'training', 'Training'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.HACKATHON)
    tagline = models.CharField(max_length=250, help_text='One-line summary shown on cards and the hero.')
    description = models.TextField(help_text='Full description. Blank lines separate paragraphs.')
    venue = models.CharField(max_length=200, default='Taita Taveta University, Voi')
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    registration_deadline = models.DateTimeField(help_text='Registrations close at this time.')
    capacity = models.PositiveIntegerField(default=0, help_text='Maximum confirmed participants. 0 means unlimited.')
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('events:detail', args=[self.slug])

    @property
    def is_past(self):
        return self.end_at < timezone.now()

    @property
    def is_upcoming(self):
        return not self.is_past

    @property
    def confirmed_count(self):
        return self.registrations.filter(status=Registration.Status.CONFIRMED).count()

    @property
    def checked_in_count(self):
        return self.registrations.filter(checked_in=True).count()

    @property
    def is_full(self):
        return self.capacity > 0 and self.confirmed_count >= self.capacity

    @property
    def spots_left(self):
        if self.capacity == 0:
            return None
        return max(self.capacity - self.confirmed_count, 0)

    @property
    def registration_open(self):
        return self.is_published and timezone.now() <= self.registration_deadline


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmed'
        WAITLISTED = 'waitlisted', 'Waitlisted'
        CANCELLED = 'cancelled', 'Cancelled'

    class Category(models.TextChoices):
        STUDENT = 'student', 'Student'
        STAFF = 'staff', 'University staff / faculty'
        PROFESSIONAL = 'professional', 'Industry professional'
        OTHER = 'other', 'Other'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    organization = models.CharField('Organization / institution', max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.STUDENT)
    ticket_code = models.CharField(max_length=20, unique=True, default=generate_ticket_code, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registered_at']
        constraints = [
            models.UniqueConstraint(fields=['event', 'email'], name='unique_registration_per_event'),
        ]

    def __str__(self):
        return f'{self.full_name} — {self.event.title}'

    def check_in(self):
        if not self.checked_in:
            self.checked_in = True
            self.checked_in_at = timezone.now()
            self.save(update_fields=['checked_in', 'checked_in_at'])

    def undo_check_in(self):
        if self.checked_in:
            self.checked_in = False
            self.checked_in_at = None
            self.save(update_fields=['checked_in', 'checked_in_at'])
