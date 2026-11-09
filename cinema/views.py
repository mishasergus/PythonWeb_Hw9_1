from django.db.models import Model
from django.shortcuts import render, redirect, get_object_or_404

from .models import Film, Category, Hall, Ticket, Review
from django.contrib import messages
from .decorators import staff_required
from .forms import FilmForm, CategoryForm, HallForm, ReviewForm

from django.contrib.auth.decorators import login_required





# Create your views here.


# HOME PAGE
def home(request):
    films = Film.objects.select_related("category").order_by("-id")[:3]
    return render(request, "cinema/home.html", {"films": films})


# LIST PAGE
def film_list(request):
    films = Film.objects.select_related("category").all()
    categories = Category.objects.all()
    q = request.GET.get("q", "").strip()
    category_name = request.GET.get("category_name", "").strip()

    if q:
        films = films.filter(name__icontains=q)
    if category_name:
        films = films.filter(category__name__iexact=category_name)

    return render(
        request,
        "cinema/film_list.html",
        {
            "films": films,
            "categories": categories,
            "selected_category": category_name,
        },
    )

def film_detail(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    reviews = film.reviews.select_related("user").order_by("-created_at")
    return render(request, "cinema/film_detail.html", {"film": film, "reviews": reviews})

# FILM EDITOR
@staff_required
def film_create(request):
    if request.method == "POST":
        form = FilmForm(request.POST)
        if form.is_valid():
            film = form.save()
            messages.success(request, "Film has been added successfully")
            return redirect("cinema:film_detail", film_id=film.id)
    else:
        form = FilmForm()
    return render(request, "cinema/film_form.html", {"form": form, "title": "New film"})

@staff_required
def film_update(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    if request.method == "POST":
        form = FilmForm(request.POST, instance=film)
        if form.is_valid():
            form.save()
            messages.success(request, "You have successfully changed film")
            return redirect("cinema:film_detail", film_id=film.id)
    else:
        form = FilmForm(instance=film)
    return render(request, "cinema/film_form.html", {"form": form, "title": f"{film} edited successfully"})

@staff_required
def film_delete(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    if request.method == "POST":
        film.delete()
        messages.success(request, "Film has deleted successfully")
        return redirect("cinema:film_list")
    return render(request, "cinema/film_confirm_delete.html", {"film": film})



# CATEGORY LIST PAGE
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'cinema/category_list.html', {"categories": categories})

def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    best_films = category.films.order_by("-rating")[:3]
    return render(request, "cinema/category_detail.html", {"category": category, "best_films": best_films})

# CATEGORY EDITOR
@staff_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, "Category has been added successfully")
            return redirect("cinema:category_detail", category_id=category.id)
    else:
        form = CategoryForm()
    return render(request, "cinema/category_form.html", {"form": form, "title": "New category"})

@staff_required
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category has been changed successfully")
            return redirect("cinema:category_detail", category_id=category.id)
    else:
        form = CategoryForm(instance=category)
    return render(request, "cinema/category_form.html", {"form": form, "title": f"{category} edited successfully"})

@staff_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category has deleted successfully")
        return redirect("cinema:category_list")
    return render(request, "cinema/category_confirm_delete.html", {"category": category})


#BOOK

@login_required
def book_ticket(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    halls = film.halls.all().order_by("name")

    return render(request, "cinema/book_ticket.html", {"film": film, "halls": halls})

@login_required
def seat_selection(request, hall_id):
    hall = get_object_or_404(Hall, id=hall_id)
    if hall.film_id is None:
        messages.error(request, "This hall is not currently showing a film.")
        return redirect("cinema:film_list")

    vip_capacity = min(max(hall.VIP_capacity, 0), max(hall.capacity, 0))
    booked_seats = set(hall.tickets.values_list("seat_number", flat=True))

    def build_seats(start, stop):
        return [
            {"number": seat_number, "booked": seat_number in booked_seats}
            for seat_number in range(start, stop + 1)
        ]

    if request.method == "POST":
        selected_seats = request.POST.getlist("selected_seats")
        selected_vip_seats = request.POST.getlist("selected_VIP_seats")
        try:
            seat_numbers = [int(seat_number) for seat_number in selected_seats]
            vip_seat_numbers = [int(seat_number) for seat_number in selected_vip_seats]
        except ValueError:
            messages.error(request, "Please select valid seats.")
        else:
            all_selected_seats = seat_numbers + vip_seat_numbers
            valid_regular_seats = all(
                vip_capacity < seat_number <= hall.capacity
                for seat_number in seat_numbers
            )
            valid_vip_seats = all(
                1 <= seat_number <= vip_capacity
                for seat_number in vip_seat_numbers
            )
            if not all_selected_seats:
                messages.error(request, "Select at least one available seat.")
            elif len(set(all_selected_seats)) != len(all_selected_seats) or not (
                valid_regular_seats and valid_vip_seats
            ):
                messages.error(request, "Please select valid seats.")
            elif booked_seats.intersection(all_selected_seats):
                messages.error(request, "One or more selected seats have already been booked.")
            else:
                Ticket.objects.bulk_create(
                    [
                        Ticket(
                            hall=hall,
                            user=request.user,
                            seat_number=seat_number,
                            seat_type=Ticket.SeatType.REGULAR,
                            price=hall.regular_price,
                        )
                        for seat_number in seat_numbers
                    ]
                    + [
                        Ticket(
                            hall=hall,
                            user=request.user,
                            seat_number=seat_number,
                            seat_type=Ticket.SeatType.VIP,
                            price=hall.vip_price,
                        )
                        for seat_number in vip_seat_numbers
                    ]
                )
                messages.success(request, "Tickets have been booked successfully.")
                return redirect("cinema:film_detail", film_id=hall.film_id)

    context = {
        "hall": hall,
        "regular_seats": build_seats(vip_capacity + 1, hall.capacity),
        "vip_seats": build_seats(1, vip_capacity),
    }
    return render(request, "cinema/seat_selection.html", context)

# HALL LIST PAGE
@staff_required
def hall_list(request):
    halls = Hall.objects.all()
    return render(request, 'cinema/hall_list.html', {"halls": halls})

@staff_required
def hall_detail(request, hall_id):
    hall = get_object_or_404(Hall, id=hall_id)
    return render(request, "cinema/hall_detail.html", {"hall": hall})

# HALL EDITOR
@staff_required
def hall_create(request):
    if request.method == "POST":
        form = HallForm(request.POST)
        if form.is_valid():
            hall = form.save()
            messages.success(request, "Hall has been added successfully")
            return redirect("cinema:hall_detail", hall_id=hall.id)
    else:
        form = HallForm()
    return render(request, "cinema/hall_form.html", {"form": form, "title": "New hall"})

@staff_required
def hall_update(request, hall_id):
    hall = get_object_or_404(Hall, id=hall_id)
    if request.method == "POST":
        form = HallForm(request.POST, instance=hall)
        if form.is_valid():
            form.save()
            messages.success(request, "Hall has been changed successfully")
            return redirect("cinema:hall_detail", hall_id=hall.id)
    else:
        form = HallForm(instance=hall)
    return render(request, "cinema/hall_form.html", {"form": form, "title": f"{hall} edited successfully"})

@staff_required
def hall_delete(request, hall_id):
    hall = get_object_or_404(Hall, id=hall_id)
    if request.method == "POST":
        hall.delete()
        messages.success(request, "Hall has been deleted successfully")
        return redirect("cinema:hall_list")
    return render(request, "cinema/hall_confirm_delete.html", {"hall": hall})

@staff_required
def hall_finish_seance(request, hall_id):
    hall = get_object_or_404(Hall, id=hall_id)
    if request.method == "POST":
        hall.tickets.all().delete()
        hall.film = None
        hall.save()
        messages.success(request, "The seance has ended and the hall is now available.")
        return redirect("cinema:hall_detail", hall_id=hall.id)
    return render(request, "cinema/hall_finish_seance.html", {"hall": hall})


@login_required()
def ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, "cinema/ticket_list.html", {"tickets": tickets})

@login_required()
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    return render(request, "cinema/ticket_detail.html", {"ticket": ticket})

@login_required()
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    if request.method == "POST":
        ticket.delete()
        messages.success(request, "Ticket has been deleted successfully")
        return redirect("cinema:ticket_list")
    return render(request, "cinema/ticket_confirm_delete.html", {"ticket": ticket})

@login_required()
def write_review(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.film = film
            review.save()
            messages.success(request, "Review has been added successfully")
            return redirect("cinema:film_detail", film_id=film.id)
    else:
        form = ReviewForm()
    return render(request, "cinema/write_review.html", {"film": film, "form": form})

