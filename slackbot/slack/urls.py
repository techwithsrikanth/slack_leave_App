from django.urls import path
from . import views
urlpatterns = [
    path('calender/', views.render_calendar, name='render_calendar'),
    path('events/', views.slack_event_handler, name='slack_event_handler'),
    path('actions/', views.slack_action_handler, name='slack_action_handler'),
]