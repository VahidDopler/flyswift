import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import BaseValidator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView

from flight.models import Flight
from user.models import MyUserModel
from .forms import CreditCardForm
from .models import Ticket, Seats
from django.core.mail import EmailMessage
from recorder.models import recordOfTickets

log = logging.getLogger(__name__)


# @login_required(login_url="http://localhost:8000/user/login/")
# def create_ticket(request):
#     try:
#         if request.method == 'POST':
#             form = TicketForm(request.POST)
#             if form.is_valid():
#                 form.save()
#                 log.info(f"ticket saved -> {form.id}")
#                 return redirect('list_of_all_ticket')
#         else:
#             form = TicketForm()
#
#     except Exception as e:
#         log.error(str(e))
#     context = {'form': form}
#     return render(request, 'tickets/create.html', context)


def send_welcome_email(user_email, ticket_messsage):
    subject = 'Report of ticket purchasing'
    message = ticket_messsage
    from_email = user_email
    recipient_list = user_email
    msg = EmailMessage(subject,
                       message, to=[from_email])
    msg.send()
    log.info(f"message send : {msg.subject}")


class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'  # Adjust the template path as needed

    def get_object(self, queryset=None):
        """
        Overriding this method to check if the requesting user owns the ticket.
        """
        ticket = super().get_object(queryset)
        if ticket.user != self.request.user:
            raise Http404("You are not authorized to view this ticket.")
        return ticket


class TicketDetailViewAll(View):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'  # Adjust the template path as needed

    def get(self, request, *args, **kwargs):
        ticket_id = kwargs["ticketNumber"]
        template = loader.get_template(self.template_name)
        try:
            ticket = Ticket.objects.get(pk=ticket_id)
            if ticket:
                return HttpResponse(template.render({'ticket': ticket}, request))
            else:
                return HttpResponse("404 , not found")
        except Exception as e:
            return HttpResponse(template.render({"error": 'Ticket does not exist'}, request))


def list_tickets(request):
    if request.user.is_authenticated:
        requested_user = request.user.id
        tickets = Ticket.objects.filter(Q(user=requested_user), active=True)
        context = {'tickets': tickets}
        return render(request, 'tickets/ticket_list.html', context)
    else:
        return render(request, "login.html", {})


# Importtant
def list_record_of_tickets(request):
    requested_user = request.user.id
    tickets = Ticket.objects.filter(Q(user=requested_user))
    context = {'tickets': tickets}
    return render(request, 'tickets/ticket_record.html', context)


class FlightDoesNotExist:
    pass


class cancelTicket(LoginRequiredMixin, View):
    login_url = "user:login"

    def get(self, request, *args, **kwargs):
        ticket_key = kwargs["tpk"]
        ticket = Ticket.objects.get(pk=ticket_key)
        user = MyUserModel.objects.get(pk=request.user.id)
        flight = Flight.objects.get(pk=ticket.flight_id)
        user.charge = int(user.charge) + (
                int(ticket.price) - (int(ticket.price) * ((100 - int(flight.cost_of_cancel)) / 100)))
        ticket.active = False
        user.save()
        ticket.save()
        return redirect("flight:feed")


class buying_ticket_page(LoginRequiredMixin, View):
    template_name = 'tickets/buying.html'
    login_url = "user:sign-in"

    def get(self, request, *args, **kwargs):
        flight_pk = kwargs["fpk"]
        template = loader.get_template(self.template_name)
        try:
            flight = Flight.objects.get(pk=flight_pk)
            if flight:
                credit_card_form = CreditCardForm()
                return HttpResponse(template.render({'flight': flight, "forms": credit_card_form}, request))
            else:
                return HttpResponse("404 , not found")
        except ObjectDoesNotExist:
            return HttpResponse("404 , not found")

    def post(self, request, *args, **kwargs):
        credit_card_value = CreditCardForm(request.POST)
        user = MyUserModel.objects.get(pk=request.user.id)
        flight = Flight.objects.get(pk=kwargs["fpk"])
        try:
            if credit_card_value.is_valid() and request.user.id and flight:
                seat_object = get_object_or_404(Seats, flightID=kwargs["fpk"], seatNumber=request.POST["seat_number"])
                if seat_object and not seat_object.isReserved:
                    seat_object.isReserved = True
                    seat_object.userReserved = request.user
                    seat_object.save()
                    result = Ticket.objects.create(user=user, flight=flight, price=int(flight.price),
                                                   seatID=seat_object)
                    result.save()
                    flight.count_of_reserved = flight.count_of_reserved + 1
                    flight.save()
                    recordOfTickets(credit_card_name=request.POST.get("credit_card_holder_name"),
                                    credit_card_month=request.POST.get("expiration_month"),
                                    credit_card_number=request.POST.get("credit_card_number"),
                                    credit_card_year=request.POST.get("expiration_year"),
                                    credit_card_ccv=request.POST.get("cvv"), ticket=result).save()

                    send_welcome_email(user.email, result.__str__())
                    log.info(f"flight {flight.id} saved")
                    return redirect('ticket:ticket_detail', pk=result.id)
                else:
                    return render(request, "tickets/buying.html",
                                  {'flight': Flight.objects.get(pk=kwargs["fpk"]), "forms": credit_card_value,
                                   'form_errors': "Your seat has been reserved , please try another seat "})
        except Exception as e:
            print("e => " + e.__str__())
            return render(request, "tickets/buying.html",
                          {'flight': Flight.objects.get(pk=kwargs["fpk"]), "forms": credit_card_value,
                           'form_errors': e})


class CheckTicket(View):
    template_name = "tickets/check_ticket.html"

    def get(self, request):
        return render(request, "tickets/check_ticket.html")

    def post(self, request, *args, **kwargs):
        print(request.POST)
        ticket_id = request.POST["ticketNumber"]
        try:
            ticket = Ticket.objects.get(pk=ticket_id)
            if ticket:
                return render(request, "tickets/ticket_detail.html", {'ticket': ticket})
            else:
                return render(request, "tickets/check_ticket.html", {'error': "Ticket not found"})
        except Exception as e:
            return render(request, "tickets/check_ticket.html", {'error': e})
