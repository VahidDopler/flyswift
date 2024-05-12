from django.urls import path

from .views import list_tickets, buying_ticket_page, cancelTicket, list_record_of_tickets, TicketDetailView, \
    TicketDetailViewAll, CheckTicket

app_name = "ticket"
urlpatterns = [
    path('all/', list_tickets, name="list_of_all_ticket_for_user"),
    path('buy/<int:fpk>/', buying_ticket_page.as_view(), name='buying_ticket'),
    path("cancel/<int:tpk>/", cancelTicket.as_view(), name="cancel_ticket"),
    path("record/", list_record_of_tickets, name="record_of_tickets"),
    path('ticket/<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('check/', CheckTicket.as_view(), name="check_ticket")
]
