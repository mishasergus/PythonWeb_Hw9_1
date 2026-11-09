from django.contrib import admin
from .models import Film, Ticket, Category, Hall

# Register your models here.

@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ("name","description","rating","img_url","category")

    readonly_fields = ("rating", )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("hall","user","seat_number","seat_type","purchased_at","price")

    readonly_fields = ("purchased_at", "hall", "user", "price", "purchased_at", )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", )

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ("name", "film", "capacity", "VIP_capacity", "regular_price", "vip_price")

    readonly_fields = ("film", )

