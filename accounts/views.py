from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.generic import View, UpdateView
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from .forms import AccountSettingsForm, SignUpForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
# TODO Add Login Required Mixins

class SignUpView(View):
    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request,user)
            return redirect('home')
        return render(request, 'signup.html', {'form': form})

    def get(self, request):
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})

class SettingsChangeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        form = AccountSettingsForm(request.POST, instance=user)
        form.save()
        messages.success(request, 'Settings successfully changed.')
        return redirect('my_account')

    def get(self,request):
        form = AccountSettingsForm()
        user = request.user
        return render(request, 'change_settings.html', {'form': form , 'user': user})

class AccountView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        context = {
            'user': user
        }
        return render(request, 'my_account.html', context)

