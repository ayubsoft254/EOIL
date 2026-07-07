from django.urls import path

from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('checkin/', views.checkin_home, name='checkin_home'),
    path('ticket/<str:ticket_code>/', views.ticket, name='ticket'),
    path('ticket/<str:ticket_code>/pdf/', views.ticket_pdf, name='ticket_pdf'),
    path('<slug:slug>/', views.event_detail, name='detail'),
    path('<slug:slug>/checkin/', views.checkin_dashboard, name='checkin'),
    path('<slug:slug>/checkin/code/', views.checkin_by_code, name='checkin_by_code'),
    path('<slug:slug>/checkin/<int:pk>/toggle/', views.checkin_toggle, name='checkin_toggle'),
    path('<slug:slug>/participants.csv', views.export_registrations_csv, name='export_csv'),
]
