from django.contrib import admin
from django.urls import path, include
from oauth_bitrix import views
from django.http import HttpResponse
from .views import install_app
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    #--------------- Ex 1--------------------------
    path('', views.oauth_status, name='home'),
    path('admin/', admin.site.urls),
    path('install/', views.install_app, name='install_app'),
    path('webhook/', views.webhook, name='webhook'),
    path('call_api/', views.call_api, name='call_api'), #Use to test in POSTMAN if oauth return in install app
    #--------------- Ex 2--------------------------------
    path('contact/new/', views.contact_form, name='contact_form'),
    path('create_contact/', views.create_contact, name='create_contact'), 
    path('contact/<int:pk>/update/', views.update_contact, name='contact_update'),
    path('contact/update/', views.contact_update_form, name='update_contact'),
    path('contact/delete/', views.contact_delete_form, name='contact_confirm_delete'),
    path('contact/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
    path('contacts/', views.contact_list, name='contact_list'),
]