from django import forms
from .models import Film, Category, Hall, Review

class FilmForm(forms.ModelForm):
    class Meta:
        model = Film
        fields = ["name", "description", "category", "img_url"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ["name", "film", "capacity", "VIP_capacity", "regular_price", "vip_price"]

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        labels = {
            "rating": "Rating (0.0 - 10.0)",
        }
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
            "rating": forms.NumberInput(attrs={"min": 0.0, "max": 10.0, "step": 0.1}),
        }