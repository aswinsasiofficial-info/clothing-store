from django import forms
from .models import Product, Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomSignupForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Full Name"
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Email Address"
        })
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data["full_name"]
        email = self.cleaned_data["email"]

        user.first_name = full_name
        user.email = email
        user.username = email  # 🔥 key part

        if commit:
            user.save()
        return user

from django.contrib.auth import authenticate

class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Email Address"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password"
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Invalid email or password")

        return cleaned_data

class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    address = forms.CharField(
    label="Address",
    widget=forms.Textarea(attrs={
        "class": "form-control",
        "rows": 5,
        "style": "resize:none;"
    })
)

    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('upi', 'UPI'),
        ('card', 'Debit/Credit Card'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES
    )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','slug','description','price','category','stock','featured','sizes','images']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','slug','description','image_url']



class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]



CANCEL_REASONS = [
    ("ordered_by_mistake", "Ordered by mistake"),
    ("found_cheaper", "Found a cheaper alternative"),
    ("delivery_too_slow", "Expected faster delivery"),
    ("wrong_address", "Entered wrong address"),
    ("changed_mind", "I changed my mind"),
    ("other", "Other reason"),
]

class CancelOrderForm(forms.Form):
    reason = forms.ChoiceField(
        choices=CANCEL_REASONS,
        widget=forms.RadioSelect,
        label="Why are you cancelling this order?"
    )
