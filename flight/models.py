from datetime import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from rest_framework import serializers

from user.models import MyUserModel
from .countries import countries
from .manager import FlightManger, AirPortManger, AirplaneManger

formatted_countries = [(country["code"], country["name"]) for country in countries]


class Airport(models.Model):
    name = models.CharField(max_length=55, default="")
    country = models.CharField(max_length=50, choices=formatted_countries, default='')
    city = models.CharField(max_length=30, default='')
    created_by_user = models.ForeignKey(MyUserModel, on_delete=models.CASCADE,
                                        null=True, blank=True, default="", verbose_name="user")
    objects = models.Manager()
    airports = AirPortManger()

    def __str__(self):
        return f"{self.name}-{self.city}"

    def to_json(self):
        return {
            'name': self.name,
            'city': self.city,
            'country': self.country,
        }


class Flight(models.Model):
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="departures")
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="arrivals")
    departure = models.DateTimeField(default=datetime.now)
    arrival = models.DateTimeField(default=datetime.now)
    price = models.PositiveIntegerField(default=0, blank=False)
    cost_of_cancel = models.PositiveIntegerField(default=0, blank=True,
                                                 validators=[MinValueValidator(0), MaxValueValidator(100)])
    airplane = models.ForeignKey('Airplane', on_delete=models.SET_NULL, null=True, related_name="flights", blank=True)
    unique_id = models.CharField(max_length=200, default=f"", blank=True)
    capacity = models.PositiveIntegerField(default=40, validators=[MinValueValidator(1), MaxValueValidator(100)])
    count_of_reserved = models.PositiveIntegerField(default=0)
    created_by_user = models.ForeignKey(MyUserModel, on_delete=models.CASCADE,
                                        null=True, blank=True, default="", verbose_name="user")
    flights = FlightManger()
    objects = models.Manager()

    def __str__(self):
        #return f"A flight from {self.origin.city} to {self.destination.city}, airplane: {self.airplane.model}, price: {self.price} created by {self.created_by_user}"
        return f"A flight from {self.origin.city} to {self.destination.city}, airplane: {self.airplane.model}"

    def get_passengers(self):
        # Get all passengers for this flight
        from ticket.models import Ticket
        passengers = Ticket.objects.filter(flight=self).values('user').distinct()

        # Map each passenger to their corresponding user
        mapped_passengers = {passenger['user']: passenger for passenger in passengers}

        return mapped_passengers

    def save(self, *args, **kwargs):
        # Set the value of the private field before saving
        self.capacity = self.airplane.capacity
        self.unique_id = f"{self.origin}-{self.destination}-{self.departure.strftime('%Y:%m:%d (%H:%M)')}-{self.arrival.strftime('%Y:%m:%d (%H:%M)')}"

        # Call the actual save method to save the instance
        super(Flight, self).save(*args, **kwargs)

    def get_available_seats(self):
        return self.capacity - self.count_of_reserved


class Airplane(models.Model):
    brand = models.CharField(max_length=50, default='')
    model = models.CharField(max_length=50, default="")
    company_name = models.CharField(max_length=60, default="")
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    created_by_user = models.ForeignKey(MyUserModel, on_delete=models.CASCADE,
                                        null=True, blank=True, default="", verbose_name="user")
    airplans = AirplaneManger()
    objects = models.Manager()

    def __str__(self):
        return f"{self.brand}-{self.model}-{self.company_name}-{self.capacity}"


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = "__all__"
