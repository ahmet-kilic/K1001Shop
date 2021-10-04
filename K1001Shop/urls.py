"""StationeryStore URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from store import views

from django.contrib import admin
from django.urls import path

from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.HomeView.as_view(), name='home'),
    path('contact/',views.ContactView.as_view(), name='contact'),
    path('product/<slug:slug>', views.ProductView.as_view(), name='product'),
    path('signup/',accounts_views.SignUpView.as_view(),name='signup'),
    path('login/', accounts_views.CustomLoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('reset/',
    auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt'
    ),
    name='password_reset'),
    path('reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
        name='password_reset_confirm'),
    path('reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
        name='password_reset_complete'),
    path('settings/password/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'),
        name='password_change'),
    path('settings/password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),
        name='password_change_done'),
    path('settings/account/', accounts_views.AccountView.as_view(), name='my_account'),
    path('settings/account/change/', accounts_views.SettingsChangeView.as_view(), name='change_settings'),
    path('addresses/', views.AddressesView.as_view(), name='addresses'),
    path('addresses/add', views.AddAddressView.as_view(), name='add_address'),
    path('addresses/remove/<int:id>/', views.DeleteAddressView.as_view(), name='delete_address'),
    path('ajax/load-subregions/', views.LoadSubregionsView.as_view() , name='ajax_load_subregions'),
    path('ajax/reviews/', views.AjaxReviewsView.as_view(), name='ajax_reviews'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('<slug:slug>/', views.HomeView.as_view(), name='category_home' ), # Problem in here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

