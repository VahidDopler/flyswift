import datetime
import logging
import uuid

import shortuuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from .forms import ChargingAccountForm as bill, MyUserCreationForm
from .models import MyUserModel, User_api_token
from user.countries import countries

log = logging.getLogger(__name__)


class UserSignUp(View):
    def get(self, req):
        if req.user.is_authenticated:
            return redirect("flight:feed")
        return render(req, "authoriziation/signup.html", {"formatted_countries": countries})

    def post(self, req):
        try:
            print(req.POST)
            if req.POST["role"] == "agency":
                email = req.POST["email"]
                password = req.POST["password1"]
                form = MyUserCreationForm(req.POST)
                if form.is_valid():
                    user = form.save()
                    email = form.cleaned_data['email']
                    password = form.cleaned_data['password1']
                    return doLogin(req, email, password)
                else:
                    return render(req, "authoriziation/signup.html", {"message": form.errors})
            else:
                print(req.POST)
                if req.POST["role"] == "normal":
                    email = req.POST["email"]
                    password = req.POST["password1"]
                    form = MyUserCreationForm(req.POST)
                    if form.is_valid():
                        user = form.save()
                        email = form.cleaned_data['email']
                        password = form.cleaned_data['password1']
                        return doLogin(req, email, password)
                    else:
                        return render(req, "authoriziation/signup.html", {"message": form.errors})
        except Exception as e:
            message = e
            return render(req, "authoriziation/signup.html", {"message": message})


class Login(View):
    def get(self, req):
        if req.user.is_authenticated:
            return redirect("flight:feed")
        return render(req, "authoriziation/login.html", {})

    def post(self, req):
        email = req.POST["email"]
        password = req.POST["password"]
        return doLogin(req, email, password)


def doLogin(req, email, password):
    authenticatedUser = authenticate(email=email, password=password)
    try:
        if not authenticatedUser:
            user = MyUserModel.objects.filter(username=email)
            raise Exception("Failed to authenticate, maybe wrong username or password")
        login(req, authenticatedUser)
        log.info(f"Login success: {email}")
        return redirect("flight:feed")
    except Exception as e:
        log.info(f"Login failed for {email}: {str(e)}")
        return render(req, "authoriziation/login.html", {"status": "fail", "message": str(e)})


class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("user:login")

    def post(self, req):
        logout(req)
        log.info("Logout success")
        return redirect("login")


class ChargingAccount(LoginRequiredMixin, View):
    login_url = "user:login"

    def get(self, request):
        form_of_billing = bill()
        return render(request, "authoriziation/charging.html", {"form": form_of_billing})

    def post(self, request):
        credit_card = {
            "cc_number": request.POST.get("credit_card_number"),
            "credit_card_holder_name": request.POST.get("credit_card_holder_name"),
            "expiration_year": request.POST.get("expiration_year"),
            "expiration_month": request.POST.get("expiration_month"),
            'cvv': request.POST.get("cvv")
        }
        credit_card_value = bill(request.POST)
        person_pk = request.user.id
        if credit_card_value.is_valid() and person_pk:
            user = MyUserModel.objects.get(pk=person_pk)
            user.charge = user.charge + int(request.POST.get("bill"))
            user.save()
            log.info(f"user saved -> {user.id}")
            return redirect("flight:feed")
        else:
            form_errors = credit_card_value.errors
            return render(request, "authoriziation/charging.html",
                          {"forms": credit_card_value,
                           'form_errors': form_errors}, )


def check_time(token):
    if datetime.date.today() > token.creation_date:
        return True
    else:
        return False


class user_info(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        try:
            user = get_object_or_404(MyUserModel, pk=request.user.id)
            token_finding = get_object_or_404(User_api_token, user=request.user)
            print(check_time(token_finding), ' checking time')
            if check_time(token_finding):
                token_finding.user_token = shortuuid.ShortUUID(alphabet="abcdefghijklmnopqrstuvwxyz-").random(length=20)
                token_finding.creation_date = datetime.date.today()
                token_finding.due_date = datetime.date.today() + datetime.timedelta(days=30)
                token_finding.save()
                return render(request, 'profile.html', {"user": user, "token": token_finding.get_user_token()})
            else:
                return render(request, 'profile.html', {"user": user, "token": token_finding.get_user_token()})
        except Exception as e:
            print(e)
            generated_token_object = User_api_token(user=request.user)
            generated_token_object.save()
            return render(request, 'profile.html',
                          {"user": request.user, "token": generated_token_object.get_user_token()})

    def post(self, request):
        user = get_object_or_404(MyUserModel, pk=request.user.id)
        token_finding = get_object_or_404(User_api_token, user=request.user)
        token_finding.user_token = shortuuid.ShortUUID(alphabet="abcdefghijklmnopqrstuvwxyz-").random(length=20)
        token_finding.creation_date = datetime.date.today()
        token_finding.due_date = datetime.date.today() + datetime.timedelta(days=30)
        token = token_finding.get_user_token()
        token_finding.save()
        return redirect('user:profile')
