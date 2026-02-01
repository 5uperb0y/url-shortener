from django.urls import path

from . import views

urlpatterns = [
    path('', views.shorten_url, name='shorten_url'),
    path('<str:query_slug>/stats/', views.summarize_clicks, name='summarize_clicks'),
    path('<str:query_slug>/', views.redirect_url, name='redirect_url'),
]
