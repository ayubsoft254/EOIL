"""Boarding-pass style PDF ticket generation with reportlab."""
import io

import qrcode
from django.utils import timezone
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

# Ticket page: 200 x 90 mm (boarding-pass format)
PAGE_W, PAGE_H = 200 * mm, 90 * mm
BAND_W = 12 * mm          # brand band on the left
STUB_X = 140 * mm         # dashed line separating the QR stub
MAIN_X = 18 * mm          # left edge of the main content area

BRAND_DARK = HexColor('#022c22')
BRAND = HexColor('#047857')
BRAND_LIGHT = HexColor('#10b981')
ACCENT = HexColor('#f59e0b')
INK = HexColor('#0f172a')
MUTED = HexColor('#64748b')
FAINT = HexColor('#cbd5e1')
AMBER_DARK = HexColor('#b45309')


def _draw_spaced(c, x, y, text, font, size, color, char_space, centered=False):
    """Draw letter-spaced text (reportlab 5 only supports charSpace on text objects)."""
    if centered:
        width = stringWidth(text, font, size) + char_space * max(len(text) - 1, 0)
        x -= width / 2
    t = c.beginText(x, y)
    t.setFont(font, size)
    t.setFillColor(color)
    t.setCharSpace(char_space)
    t.textOut(text)
    c.drawText(t)


def _fit_text(text, font, size, max_width):
    """Truncate text with an ellipsis so it fits max_width."""
    if stringWidth(text, font, size) <= max_width:
        return text
    while text and stringWidth(text + '…', font, size) > max_width:
        text = text[:-1]
    return text + '…'


def _wrap_title(title, font, size, max_width):
    """Wrap a title into at most two lines, truncating the second."""
    words = title.split()
    lines, current = [], ''
    for word in words:
        candidate = f'{current} {word}'.strip()
        if stringWidth(candidate, font, size) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) == 2:
                break
    if current and len(lines) < 2:
        lines.append(current)
    if len(lines) == 2:
        lines[1] = _fit_text(lines[1], font, size, max_width)
    return lines


def _event_date_str(event):
    start = timezone.localtime(event.start_at)
    end = timezone.localtime(event.end_at)
    if start.date() == end.date():
        return f'{start:%a, %d %b %Y} · {start:%H:%M}–{end:%H:%M}'
    return f'{start:%d %b} – {end:%d %b %Y} · from {start:%H:%M}'


def _qr_image(data):
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return ImageReader(buffer)


def _label_value(c, x, y, label, value, value_font='Helvetica-Bold',
                 value_size=9, value_color=INK, max_width=52 * mm):
    _draw_spaced(c, x, y, label.upper(), 'Helvetica-Bold', 5.5, MUTED, 0.7)
    c.setFont(value_font, value_size)
    c.setFillColor(value_color)
    c.drawString(x, y - 4.6 * mm, _fit_text(value, value_font, value_size, max_width))


def build_ticket_pdf(registration):
    """Render a registration as a single-page PDF ticket; returns bytes."""
    event = registration.event
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f'Ticket {registration.ticket_code} — {event.title}')

    # Background + outer border
    c.setFillColor(HexColor('#ffffff'))
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Left brand band with vertical lettering
    c.setFillColor(BRAND_DARK)
    c.rect(0, 0, BAND_W, PAGE_H, stroke=0, fill=1)
    c.saveState()
    c.translate(BAND_W / 2 + 1.2 * mm, PAGE_H / 2)
    c.rotate(90)
    _draw_spaced(c, 0, 0, 'EARTH OBSERVATION INNOVATION LABORATORY',
                 'Helvetica-Bold', 6, HexColor('#6ee7b7'), 1.6, centered=True)
    c.restoreState()

    # Accent baseline under the main area
    c.setFillColor(ACCENT)
    c.rect(BAND_W, 0, PAGE_W - BAND_W, 1.6 * mm, stroke=0, fill=1)

    # Header: organisation + event-type chip
    _draw_spaced(c, MAIN_X, 79 * mm, 'EOIL · TAITA TAVETA UNIVERSITY',
                 'Helvetica-Bold', 8, BRAND, 0.6)

    chip_label = event.get_event_type_display().upper()
    chip_w = stringWidth(chip_label, 'Helvetica-Bold', 7) + 6 * mm
    chip_x = STUB_X - 4 * mm - chip_w
    c.setFillColor(ACCENT)
    c.roundRect(chip_x, 77 * mm, chip_w, 6 * mm, 3 * mm, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 7)
    c.drawCentredString(chip_x + chip_w / 2, 79 * mm, chip_label)

    # Event title (up to two lines)
    title_font, title_size = 'Helvetica-Bold', 15
    title_max = chip_x - MAIN_X - 4 * mm
    lines = _wrap_title(event.title, title_font, title_size, max(title_max, 80 * mm))
    c.setFillColor(INK)
    c.setFont(title_font, title_size)
    title_y = 70 * mm
    for line in lines:
        c.drawString(MAIN_X, title_y, line)
        title_y -= 6.5 * mm

    # Divider
    c.setStrokeColor(FAINT)
    c.setLineWidth(0.6)
    c.line(MAIN_X, 56 * mm, STUB_X - 4 * mm, 56 * mm)

    # Details grid
    _label_value(c, MAIN_X, 50 * mm, 'Date & time', _event_date_str(event),
                 max_width=58 * mm)
    _label_value(c, 82 * mm, 50 * mm, 'Venue', event.venue,
                 value_size=8, max_width=54 * mm)

    _label_value(c, MAIN_X, 34 * mm, 'Participant', registration.full_name,
                 value_size=10, max_width=58 * mm)
    c.setFont('Helvetica', 7)
    c.setFillColor(MUTED)
    c.drawString(MAIN_X, 25.5 * mm, _fit_text(registration.email, 'Helvetica', 7, 58 * mm))

    _label_value(c, 82 * mm, 34 * mm, 'Category',
                 registration.get_category_display(), max_width=34 * mm)
    if registration.status == 'confirmed':
        status_label, status_color = 'CONFIRMED', BRAND
    elif registration.status == 'waitlisted':
        status_label, status_color = 'WAITLISTED', AMBER_DARK
    else:
        status_label, status_color = 'CANCELLED', HexColor('#b91c1c')
    _label_value(c, 118 * mm, 34 * mm, 'Status', status_label,
                 value_size=8.5, value_color=status_color, max_width=20 * mm)

    # Footer note
    c.setFont('Helvetica', 6)
    c.setFillColor(MUTED)
    c.drawString(MAIN_X, 7 * mm,
                 'Present this ticket (printed or on your phone) at the check-in desk.')

    # Dashed stub separator
    c.setStrokeColor(FAINT)
    c.setLineWidth(0.8)
    c.setDash(3, 3)
    c.line(STUB_X, 5 * mm, STUB_X, 85 * mm)
    c.setDash()

    # Stub: ADMIT ONE, QR, code, contact
    stub_center = (STUB_X + PAGE_W) / 2
    _draw_spaced(c, stub_center, 80 * mm, 'ADMIT ONE',
                 'Helvetica-Bold', 7, BRAND, 2, centered=True)

    qr_size = 34 * mm
    c.drawImage(_qr_image(registration.ticket_code),
                stub_center - qr_size / 2, 40 * mm, qr_size, qr_size)

    c.setFont('Courier-Bold', 11)
    c.setFillColor(INK)
    c.drawCentredString(stub_center, 32 * mm, registration.ticket_code)
    c.setFont('Helvetica-Bold', 7)
    c.setFillColor(status_color)
    c.drawCentredString(stub_center, 25 * mm, status_label)
    c.setFont('Helvetica', 5.5)
    c.setFillColor(MUTED)
    c.drawCentredString(stub_center, 8 * mm, 'eoil@ttu.ac.ke · ttu.ac.ke')

    c.showPage()
    c.save()
    return buffer.getvalue()
