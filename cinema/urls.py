from django.urls import path
from . import views

app_name = 'cinema'

urlpatterns = [
    path('', views.home, name='home'),
    path('cinema/', views.film_list, name='film_list'),
    path('cinema/add/', views.film_create, name='film_create'),
    path('cinema/<int:film_id>/', views.film_detail, name='film_detail'),
    path('cinema/<int:film_id>/review/', views.write_review, name='write_review'),
    path('cinema/<int:film_id>/book/', views.book_ticket, name='book_ticket'),
    path('halls/<int:hall_id>/seats/', views.seat_selection, name='seat_selection'),
    path('cinema/<int:film_id>/edit/', views.film_update, name='film_update'),
    path('cinema/<int:film_id>/delete/', views.film_delete, name='film_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('categories/<int:category_id>/edit/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('halls/', views.hall_list, name='hall_list'),
    path('halls/add/', views.hall_create, name='hall_create'),
    path('halls/<int:hall_id>/', views.hall_detail, name='hall_detail'),
    path('halls/<int:hall_id>/edit/', views.hall_update, name='hall_update'),
    path('halls/<int:hall_id>/delete/', views.hall_delete, name='hall_delete'),
    path('halls/<int:hall_id>/finish-seance/', views.hall_finish_seance, name='hall_finish_seance'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/delete/', views.ticket_delete, name='ticket_delete'),
]