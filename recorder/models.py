import datetime

from django.db import models

from ticket.models import Ticket


# Create your models here.

class recordOfTickets(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.DO_NOTHING, verbose_name="Field of ticket")
    credit_card_number = models.CharField(max_length=16)
    credit_card_name = models.CharField(max_length=80)
    credit_card_ccv = models.CharField(max_length=3)
    credit_card_year = models.CharField(max_length=4)
    credit_card_month = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.credit_card_name} : {self.ticket}"
