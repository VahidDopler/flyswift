import datetime
import logging
import time

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django.core import serializers

from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView
import json
from ticket.models import Seats
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, FormView

from flight.forms import FlightForm, AirplaneForm
from flight.models import Flight, Airport, Airplane
from ticket.models import Ticket
from flight.countries import countries

log = logging.getLogger(__name__)


def index(request):
    if request.user.is_authenticated:
        return render(request, "home.html", {"user": request.user})
    else:
        return redirect("user:login")


def get_passengers_for_flight(flight_id):
    passengers = (
        Ticket.objects
        .filter(flight_id=flight_id)
        .values('user')
        .distinct()
    )

    return [passenger['user'] for passenger in passengers]


class FlightListView(LoginRequiredMixin, ListView):
    model = Flight
    template_name = 'flight/all_flights.html'
    login_url = "user:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        flights = Flight.objects.all()

        flight_passenger_info = []
        available_seats = []
        for flight in flights:
            passengers = get_passengers_for_flight(flight.id)
            flight_passenger_info.append((flight, passengers))
            available_seats.append(flight.get_available_seats())
        context['flight_passenger_info'] = flight_passenger_info
        return context


def search_flights(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            try:
                city_origin = request.POST.get('cityOrigin')
                city_destination = request.POST.get('cityDestination')
                flights = Flight.objects.all()
                if city_destination and city_origin:
                    flights = flights.filter(origin__city__contains=city_origin,
                                             destination__city__contains=city_destination)
                if city_origin:
                    flights = flights.filter(origin__city__contains=city_origin)

                if city_destination:
                    flights = flights.filter(destination__city__contains=city_destination)

                context = {"flights": flights}
                return render(request, 'flight/search.html', context)

            except Exception as e:
                log.error(f"search failed {str(e)}")
        return render(request, 'flight/search.html')


class FlightView(LoginRequiredMixin, View):
    login_url = "user:login"

    def get(self, request, flight_id):
        print(flight_id)
        try:
            flight = get_object_or_404(Flight, pk=flight_id)
            print(flight)
            return render(request, 'flight/flight.html', {'flight': flight})
        except Exception as e:
            print(e)
            return redirect("flight:feed")


class FlightCreateView(LoginRequiredMixin, FormView):
    model = Flight
    template_name = 'flight/createflight.html'
    form_class = FlightForm
    success_url = reverse_lazy('flight_list')
    login_url = "user:login"

    def post(self, request, *args, **kwargs):
        form = FlightForm(request.POST)
        try:
            if form.is_valid():
                # 'origin': ['6'], 'destination': ['7'], 'departure': ['2024-04-04T20:43'],
                # 'arrival': ['2024-05-21T20:43'], 'price': ['3600'], 'cost_of_cancel': ['25'], 'airplane': ['4']}>
                if request.POST["origin"] == request.POST["destination"]:
                    raise Exception("your origin and destination are same")
                departure_str = request.POST["departure"]
                arrival_str = request.POST["arrival"]

                # Convert string representations to datetime objects
                departure_time = datetime.datetime.strptime(departure_str, "%Y-%m-%dT%H:%M")
                arrival_time = datetime.datetime.strptime(arrival_str, "%Y-%m-%dT%H:%M")

                # Get current time (considering timezone if necessary)
                current_time = datetime.datetime.now() # Use timezone.now() if using Django

                # Perform validation checks
                if departure_time < current_time:
                    raise Exception("Departure time cannot be in the past. Please choose a future time.")

                if arrival_time < current_time:
                    raise Exception("Arrival time cannot be in the past. Please choose a future time.")

                if departure_time >= arrival_time:
                    raise Exception("Arrival time must be later than departure time. Please adjust your times.")
                # flight = Flight(origin=form.cleaned_data.get("origin"),
                #                 destination=form.cleaned_data.get("destination"),
                #                 departure=form.cleaned_data.get("departure"),
                #                 arrival=form.cleaned_data.get("arrival"),
                #                 airplane=form.cleaned_data.get("airplane"),
                #                 cost_of_cancel=form.cleaned_data.get("cost_of_cancel"),
                #                 price=form.cleaned_data.get("price"),
                #                 created_by_user=request.user)
                # flight.save()
                # for x in range(flight.capacity):
                #     Seats(flightID=flight, seatNumber=x + 1).save()
                # log.info(f"saved flight -> {flight.id}")
                return redirect("flight:all_flights")
            else:
                Airports = Airport.objects.all()
                airplanes = Airplane.objects.all()
                template = loader.get_template(self.template_name)
                return HttpResponse(
                    template.render(
                        {"airports": Airports, "airplanes": airplanes, "errors": form.errors},
                        request))
        except Exception as e:
            log.error(str(e))
            print(e)
            airports = Airport.objects.filter(created_by_user=request.user)
            airplanes = Airplane.objects.filter(created_by_user=request.user)
            context = {
                "airports": airports,
                "airplanes": airplanes,
                "errors": e.__str__()
            }
            return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            airports = Airport.objects.filter(created_by_user=request.user)
            airplanes = Airplane.objects.filter(created_by_user=request.user)
            context = {
                "airports": airports,
                "airplanes": airplanes,
            }
            return self.render_to_response(context)
        else:
            return redirect("user:login")


class CreateAirplaneView(LoginRequiredMixin, FormView):
    model = Flight
    template_name = 'flight/createairplane.html'
    form_class = FlightForm
    success_url = reverse_lazy('flight_list')
    login_url = "user:login"

    def post(self, request, *args, **kwargs):
        try:
            form = AirplaneForm(request.POST)
            if form.is_valid():
                airplane = form.save(commit=False)  # Don't save just yet
                airplane.created_by_user = request.user  # Add the current user
                airplane.save()
                log.info(f"saved airplane -> {airplane.id}")
                return redirect("flight:feed")
            raise Exception(form.errors)
        except Exception as e:
            template = loader.get_template(self.template_name)
            return HttpResponse(
                template.render(
                    {"form": AirplaneForm(request.POST), "errors": AirplaneForm(request.POST).errors},
                    request))

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            airplaneForm = AirplaneForm()
            context = {
                "form": airplaneForm,
            }
            return self.render_to_response(context)
        else:
            return redirect("user:login")


def user_tickets(request):
    return redirect('list_of_all_ticket_for_user')


def create_airport(request):
    if request.user.is_authenticated:
        if request.user.role == "normal":
            return redirect("flight:feed")
        elif request.method == 'GET':
            return render(request, 'airport/create_airport.html', {"formatted_countries": countries})
        elif request.method == 'POST':
            city = request.POST.get("city") or None
            country = request.POST.get("country") or None
            name = request.POST.get("name") or None
            if city and country and name:
                new_airport = Airport.objects.create(created_by_user=request.user, name=name, country=country,
                                                     city=city)
                new_airport.save()
                return redirect('flight:create_airport')
        else:
            return render(request, 'airport/create_airport.html', {"formatted_countries": countries})


def search_flights_byDate(request):
    if request.user.is_authenticated:
        print(request.POST)
        if request.method == "POST":
            try:
                startdate = request.POST.get('startdate')
                flights = Flight.objects.filter(departure__gte=startdate)
                context = {"flights": flights}
                return render(request, 'flight/search_flight_date.html', context)

            except Exception as e:
                log.error(f"search failed {str(e)}")
        return render(request, 'flight/search_flight_date.html')


class FlightModelSerializer(ModelSerializer):
    class Meta:
        model = Flight
        fields = "__all__"


class getAllFlightrest(APIView):
    def get(self, request, *args, **kwargs):
        if request.method == "GET":
            print(json.loads(json.dumps(request.data)))
            # flight = get_object_or_404(Flight, pk=request.data["flightid"])
            # serializer = FlightModelSerializer(flight)
            # data = serializer.data
            all_flight = Flight.objects.all()
            serialzed_object = serializers.serialize("jsonl", all_flight)
            return HttpResponse(json.dumps(serialzed_object, indent=0), content_type='application/json')


class search_flight_byDate_api(APIView):
    def get(self, request):
        try:
            if request.method == "GET":
                flights = object
                if request.POST.get('startdate') and request.POST.get("finishdate"):
                    flights = Flight.objects.filter(departure__gte=request.POST.get('startdate'),
                                                    arrival__lte=request.POST.get("finishdate"))
                if request.POST.get('startdate'):
                    flights = Flight.objects.filter(departure__gte=request.POST.get('startdate'))
                if request.POST.get("finishdate"):
                    flights = Flight.objects.filter(arrival__lte=request.POST.get("finishdate"))
                if flights:
                    serialized_object = serializers.serialize("jsonl", flights)
                    return HttpResponse(json.dumps(serialized_object, indent=0), content_type='application/json')
                else:
                    return HttpResponse(json.dumps({"status ": "bad request"}, indent=0),
                                        content_type='application/json')
        except Exception as e:
            return HttpResponse(json.dumps({"status ": f"{e.__str__()}"}, indent=0),
                                content_type='application/json')
