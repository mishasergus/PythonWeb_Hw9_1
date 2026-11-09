from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Film(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True)
    description = models.TextField()

    img_url = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='films'
    )

    @property
    def rating(self):

        result = self.reviews.aggregate(avg_rating=Avg('rating'))
        return round(result['avg_rating'] or 0.0, 1)

    def __str__(self):
        return self.name


class Hall(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True)
    film = models.ForeignKey(
        Film,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='halls'
    )
    capacity = models.IntegerField(default=100)
    VIP_capacity = models.IntegerField(default=20)

    regular_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10.00
    )

    vip_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=15.00
    )

    def __str__(self):
        film_name = self.film.name if self.film_id else "No film assigned"
        return f"{self.name} (Фільм: {film_name}) [Зв: {self.regular_price}, VIP: {self.vip_price}]"


class Ticket(models.Model):
    class SeatType(models.TextChoices):
        REGULAR = 'REGULAR', 'Звичайне (Regular)'
        VIP = 'VIP', 'VIP'

    id = models.AutoField(primary_key=True)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')

    seat_number = models.IntegerField(default=1)
    seat_type = models.CharField(
        max_length=10,
        choices=SeatType.choices,
        default=SeatType.REGULAR
    )

    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    purchased_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.seat_type == self.SeatType.VIP:
            self.price = self.hall.vip_price
        else:
            self.price = self.hall.regular_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket ({self.seat_type}) | Hall: {self.hall.name} | Seat: {self.seat_number} | Price: {self.price}$ - User: {self.user.username}"


class Review(models.Model):
    id = models.AutoField(primary_key=True)
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.film.name} by {self.user.username} - Rating: {self.rating}"