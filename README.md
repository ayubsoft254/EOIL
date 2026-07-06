# EOIL @ Taita Taveta University

Website for the **Earth Observation Innovation Laboratory (EOIL)** hub at Taita Taveta
University — part of the [Kenya Space Agency EOIL programme](https://ksa.go.ke/eoil)
commissioned by the European Union & France and implemented by Expertise France.

Built with **Django** and **Tailwind CSS**.

## Features

- **Landing page** — mission, objectives, thematic focus areas, services, targets and partners.
- **Event management** — hackathons, conferences, workshops and trainings:
  - Public event listing and detail pages.
  - Participant registration with capacity limits and automatic **waitlisting** when full.
  - Digital **tickets** with a unique code and QR code, emailed on registration.
  - Staff-only **check-in desk** (`/events/checkin/`): live stats, search, one-click
    check-in/undo, and quick check-in by typing or scanning a ticket code.
  - CSV export of participants (dashboard button or Django admin action).
- **Newsletter** — footer signup on every page, one-click unsubscribe links, and an admin
  action to compose and send issues to all active subscribers.

## Getting started

```powershell
# 1. Create a virtualenv and install dependencies
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# 2. Set up the database
.\venv\Scripts\python manage.py migrate

# 3. Create an admin/staff account
.\venv\Scripts\python manage.py createsuperuser

# 4. (Optional) load demo events and registrations
.\venv\Scripts\python manage.py seed_demo

# 5. Run the dev server
.\venv\Scripts\python manage.py runserver
```

Then open <http://127.0.0.1:8000>.

| URL | Purpose |
| --- | --- |
| `/` | Landing page |
| `/events/` | Event listing (upcoming + past) |
| `/events/<slug>/` | Event detail + registration form |
| `/events/ticket/<code>/` | Participant's digital ticket (QR) |
| `/events/checkin/` | Staff check-in desk (login required) |
| `/admin/` | Django admin — events, registrations, subscribers, newsletter issues |

## Managing events

Create and edit events in the Django admin (**Events → Events**). Registration closes
automatically at the deadline; setting *capacity* to `0` means unlimited attendance.
Registrations can be managed per event (inline) or in bulk under **Events → Registrations**,
with admin actions for check-in and CSV export.

## Sending a newsletter

1. In the admin, create a **Newsletter issue** (subject + body).
2. Select it in the list and run the action *"Send selected issue(s) to active subscribers"*.

Emails use the **console backend** in development (they print to the terminal). For
production, configure an SMTP backend in `config/settings.py`.

## Production notes

- Tailwind is loaded from the Play CDN for development. For production, compile a static
  stylesheet with the [Tailwind CLI](https://tailwindcss.com/docs/installation) and replace
  the `<script src="https://cdn.tailwindcss.com">` block in `templates/base.html`.
- Set `DEBUG = False`, a real `SECRET_KEY`, `ALLOWED_HOSTS`, and an SMTP `EMAIL_BACKEND`.
- Serve `media/` (event banners) and collected static files from your web server.
