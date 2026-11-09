from django.test import TestCase

from django.contrib.auth.models import User
from django.urls import reverse

from .models import Category, Film, Hall, Review, Ticket


class TicketBookingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viewer", password="password")
        category = Category.objects.create(name="Drama")
        self.film = Film.objects.create(
            name="The Frame",
            description="A film description.",
            img_url="",
            category=category,
        )
        self.hall = Hall.objects.create(
            name="Hall 1",
            film=self.film,
            capacity=10,
            VIP_capacity=2,
            regular_price=10,
            vip_price=15,
        )

    def test_film_detail_has_book_button(self):
        response = self.client.get(reverse("cinema:film_detail", args=[self.film.id]))

        self.assertContains(
            response,
            reverse("cinema:book_ticket", args=[self.film.id]),
        )

    def test_film_detail_shows_reviews_and_average_rating(self):
        Review.objects.create(
            film=self.film,
            user=self.user,
            rating="8.5",
            comment="A great film.",
        )

        response = self.client.get(reverse("cinema:film_detail", args=[self.film.id]))

        self.assertContains(response, "Reviews")
        self.assertContains(response, "(1)")
        self.assertContains(response, "A great film.")
        self.assertContains(response, "8.5/10")
        self.assertContains(response, "★ 8.5")

    def test_review_submission_requires_login_and_saves_for_current_film(self):
        review_url = reverse("cinema:write_review", args=[self.film.id])
        response = self.client.get(review_url)
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={review_url}",
        )

        self.client.force_login(self.user)
        response = self.client.get(review_url)
        self.assertContains(response, "Review The Frame")
        self.assertNotContains(response, 'name="film"')

        response = self.client.post(
            review_url,
            {"rating": "9.0", "comment": "Worth seeing."},
        )

        self.assertRedirects(
            response,
            reverse("cinema:film_detail", args=[self.film.id]),
        )
        review = Review.objects.get()
        self.assertEqual(review.film, self.film)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.comment, "Worth seeing.")

    def test_booking_flow_requires_login_and_books_selected_seat(self):
        booking_url = reverse("cinema:book_ticket", args=[self.film.id])
        response = self.client.get(booking_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={booking_url}")

        self.client.force_login(self.user)
        response = self.client.get(booking_url)
        self.assertContains(response, reverse("cinema:seat_selection", args=[self.hall.id]))
        response = self.client.get(reverse("cinema:seat_selection", args=[self.hall.id]))
        self.assertContains(response, 'name="selected_VIP_seats" value="1"')

        response = self.client.post(
            reverse("cinema:seat_selection", args=[self.hall.id]),
            {"selected_VIP_seats": ["1"]},
        )

        self.assertRedirects(response, reverse("cinema:film_detail", args=[self.film.id]))
        ticket = Ticket.objects.get()
        self.assertEqual(ticket.seat_number, 1)
        self.assertEqual(ticket.seat_type, Ticket.SeatType.VIP)
        self.assertEqual(ticket.price, self.hall.vip_price)

    def test_booked_seats_are_disabled_and_cannot_be_booked_again(self):
        Ticket.objects.create(
            hall=self.hall,
            user=self.user,
            seat_number=1,
            seat_type=Ticket.SeatType.VIP,
            price=self.hall.vip_price,
        )
        self.client.force_login(self.user)
        url = reverse("cinema:seat_selection", args=[self.hall.id])

        response = self.client.get(url)
        self.assertContains(response, 'name="selected_VIP_seats" value="1"')
        self.assertContains(response, 'disabled aria-label="VIP seat 1 booked"')
        self.assertContains(response, 'name="selected_VIP_seats" value="2"')

        response = self.client.post(url, {"selected_VIP_seats": ["1"]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.filter(hall=self.hall).count(), 1)
        self.assertContains(response, "already been booked")

    def test_staff_can_create_and_edit_halls(self):
        staff_user = User.objects.create_user(
            username="manager",
            password="password",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        list_url = reverse("cinema:hall_list")
        response = self.client.get(list_url)
        self.assertContains(response, self.hall.name)
        self.assertContains(
            response,
            reverse("cinema:hall_finish_seance", args=[self.hall.id]),
        )
        create_url = reverse("cinema:hall_create")
        self.assertEqual(self.client.get(create_url).status_code, 200)

        response = self.client.post(
            create_url,
            {
                "name": "Hall 2",
                "film": self.film.id,
                "capacity": 20,
                "VIP_capacity": 5,
                "regular_price": "12.00",
                "vip_price": "18.00",
            },
        )
        new_hall = Hall.objects.get(name="Hall 2")
        self.assertRedirects(
            response,
            reverse("cinema:hall_detail", args=[new_hall.id]),
        )

        edit_url = reverse("cinema:hall_update", args=[new_hall.id])
        self.assertContains(self.client.get(edit_url), "Save hall")
        response = self.client.post(
            edit_url,
            {
                "name": "Hall 2",
                "film": self.film.id,
                "capacity": 25,
                "VIP_capacity": 5,
                "regular_price": "12.00",
                "vip_price": "18.00",
            },
        )
        new_hall.refresh_from_db()
        self.assertEqual(new_hall.capacity, 25)
        self.assertRedirects(
            response,
            reverse("cinema:hall_detail", args=[new_hall.id]),
        )

    def test_ticket_pages_and_cancellation(self):
        ticket = Ticket.objects.create(
            hall=self.hall,
            user=self.user,
            seat_number=1,
            seat_type=Ticket.SeatType.VIP,
            price=self.hall.vip_price,
        )
        self.client.force_login(self.user)

        list_url = reverse("cinema:ticket_list")
        self.assertContains(self.client.get(list_url), self.film.name)
        detail_url = reverse("cinema:ticket_detail", args=[ticket.id])
        self.assertContains(self.client.get(detail_url), "Seat:")

        response = self.client.post(reverse("cinema:ticket_delete", args=[ticket.id]))

        self.assertRedirects(response, list_url)
        self.assertFalse(Ticket.objects.filter(id=ticket.id).exists())

    def test_staff_can_finish_seance_without_deleting_hall_or_film(self):
        ticket = Ticket.objects.create(
            hall=self.hall,
            user=self.user,
            seat_number=1,
            seat_type=Ticket.SeatType.VIP,
            price=self.hall.vip_price,
        )
        staff_user = User.objects.create_user(
            username="manager",
            password="password",
            is_staff=True,
        )
        self.client.force_login(staff_user)
        finish_url = reverse("cinema:hall_finish_seance", args=[self.hall.id])
        self.assertContains(self.client.get(finish_url), "Finish this seance?")

        response = self.client.post(finish_url)

        self.assertRedirects(
            response,
            reverse("cinema:hall_detail", args=[self.hall.id]),
        )
        self.assertFalse(Ticket.objects.filter(id=ticket.id).exists())
        self.assertTrue(Hall.objects.filter(id=self.hall.id).exists())
        self.assertTrue(Film.objects.filter(id=self.film.id).exists())
        self.hall.refresh_from_db()
        self.assertIsNone(self.hall.film_id)
        self.assertContains(
            self.client.get(reverse("cinema:hall_detail", args=[self.hall.id])),
            "No film is currently assigned",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("cinema:seat_selection", args=[self.hall.id]))
        self.assertRedirects(response, reverse("cinema:film_list"))
        self.client.force_login(staff_user)
        self.assertEqual(
            self.client.get(reverse("cinema:hall_update", args=[self.hall.id])).status_code,
            200,
        )
