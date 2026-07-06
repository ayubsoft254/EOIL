"""Seed the database with demo events and registrations for local development."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event, Registration
from newsletter.models import Subscriber


class Command(BaseCommand):
    help = 'Create demo events, registrations and newsletter subscribers.'

    def handle(self, *args, **options):
        now = timezone.now()

        hackathon, _ = Event.objects.get_or_create(
            slug='tsavo-eo-hackathon-2026',
            defaults=dict(
                title='Tsavo EO Hackathon 2026',
                event_type=Event.EventType.HACKATHON,
                tagline='48 hours building satellite-data solutions for wildlife, water and farms in the Tsavo ecosystem.',
                description=(
                    'Join innovators from across the coast region for a 48-hour hackathon at the '
                    'EOIL lab. Teams will use free satellite imagery and open-source geospatial tools '
                    'to prototype solutions to challenges posed by county governments, KWS and local '
                    'farmer cooperatives.\n\n'
                    'Tracks include drought early warning, human-wildlife conflict mapping, and '
                    'mining-site rehabilitation monitoring. Mentors from the Kenya Space Agency and '
                    'Expertise France will be on site, and the top three teams enter the EOIL '
                    'incubation programme.\n\n'
                    'Bring a laptop; food, data access and workstations are provided. Open to '
                    'students, researchers and professionals — no prior EO experience required.'
                ),
                venue='EOIL Lab, Taita Taveta University, Voi',
                start_at=now + timedelta(days=21),
                end_at=now + timedelta(days=23),
                registration_deadline=now + timedelta(days=18),
                capacity=80,
            ),
        )

        conference, _ = Event.objects.get_or_create(
            slug='eo-for-counties-conference-2026',
            defaults=dict(
                title='EO for Counties Conference 2026',
                event_type=Event.EventType.CONFERENCE,
                tagline='A two-day conference connecting county planners with Earth-observation science and tools.',
                description=(
                    'The annual EOIL conference brings together county government officers, '
                    'researchers, and industry to showcase how satellite data is transforming '
                    'planning and service delivery in Kenya.\n\n'
                    'Expect keynotes from the Kenya Space Agency, technical sessions on land-use '
                    'mapping and climate services, and a demo floor of EO start-ups incubated at '
                    'Taita Taveta University and the University of Nairobi.'
                ),
                venue='Taita Taveta University Main Auditorium, Voi',
                start_at=now + timedelta(days=45),
                end_at=now + timedelta(days=46),
                registration_deadline=now + timedelta(days=40),
                capacity=250,
            ),
        )

        workshop, _ = Event.objects.get_or_create(
            slug='intro-to-remote-sensing-workshop',
            defaults=dict(
                title='Intro to Remote Sensing Workshop',
                event_type=Event.EventType.WORKSHOP,
                tagline='A hands-on beginner workshop on QGIS and free satellite imagery.',
                description=(
                    'A one-day, hands-on introduction to remote sensing for absolute beginners. '
                    'Participants learned to find free Sentinel-2 imagery, load it in QGIS, and '
                    'produce a simple land-cover map of Voi town.'
                ),
                venue='EOIL Lab, Taita Taveta University, Voi',
                start_at=now - timedelta(days=30),
                end_at=now - timedelta(days=30, hours=-8),
                registration_deadline=now - timedelta(days=33),
                capacity=40,
            ),
        )

        demo_people = [
            ('Amina Mwadime', 'amina@example.com', Registration.Category.STUDENT, True),
            ('Brian Kilonzo', 'brian@example.com', Registration.Category.STUDENT, False),
            ('Cynthia Wanjala', 'cynthia@example.com', Registration.Category.PROFESSIONAL, True),
            ('Daniel Mwangeka', 'daniel@example.com', Registration.Category.STAFF, False),
            ('Esther Nyambura', 'esther@example.com', Registration.Category.OTHER, False),
        ]
        for name, email, category, checked_in in demo_people:
            reg, created = Registration.objects.get_or_create(
                event=hackathon, email=email,
                defaults=dict(full_name=name, category=category,
                              organization='Taita Taveta University'),
            )
            if created and checked_in:
                reg.check_in()

        Subscriber.objects.get_or_create(email='subscriber@example.com',
                                         defaults=dict(name='Demo Subscriber'))

        self.stdout.write(self.style.SUCCESS(
            f'Seeded: {Event.objects.count()} events, '
            f'{Registration.objects.count()} registrations, '
            f'{Subscriber.objects.count()} subscribers.'))
