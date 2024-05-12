import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

import flight
import user.models
from flight.models import Flight
from user.models import MyUserModel
from .manager import TicketManger

string_checker = "No user reserved"


class Seats(models.Model):
    flightID = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="Flight_rel",
                                 verbose_name="id to flight", null=True , blank=True)
    userReserved = models.ForeignKey(MyUserModel, on_delete=models.CASCADE, related_name="user_rel",
                                     verbose_name="id to user", null=True , blank=True)
    seatNumber = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], null=True,
                                             blank=True)
    isReserved = models.BooleanField(default=False, blank=True)


class Ticket(models.Model):
    user = models.ForeignKey(MyUserModel, on_delete=models.CASCADE, related_name="tickets", blank=True, null=True)
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="flight", blank=True, null=True)
    price = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(999999999)], null=True,
                                        blank=True)
    unique_id = models.CharField(max_length=500, default='', blank=True, null=True)
    active = models.BooleanField(default=True, verbose_name="being status : ")
    seatID = models.ForeignKey(Seats, on_delete=models.DO_NOTHING, verbose_name="seat ticket id", blank=True, null=True)
    tickets = TicketManger()
    objects = models.Manager()

    def save(self, *args, **kwargs):
        # self.unique_id = f'{self.user}-{self.flight.id}-{self.flight.__str__()}-{self.seatID.seatNumber}-{self.flight.airplane.id}-{self.flight.arrival}'\
        self.unique_id = uuid.uuid4().__hash__()
        # self.id = uuid.uuid4().__hash__()

        super(Ticket, self).save(*args, **kwargs)

    def __str__(self):
        return f"Ticket ( {self.unique_id} ) for {self.user.full_name} with sent number : {self.seatID.seatNumber} on flight {self.flight}"
