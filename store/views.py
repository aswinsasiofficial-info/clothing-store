from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Product, Category, Order, OrderItem,Wishlist
from .forms import CheckoutForm, CancelOrderForm,ProfileForm
from django.utils import timezone
from django.db import transaction
import random
import stringf
import razorpay
from django.conf import settings
from django.http import JsonResponse
from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib import messages
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.http import HttpResponse
from datetime import timedelta
from django.contrib.auth.models import User
from .forms import CustomSignupForm, EmailLoginForm

def login_view(request):
    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(username=email, password=password)
            login(request, user)
            return redirect("store:home")
    else:
        form = EmailLoginForm()

    return render(request, "store/login.html", {"form": form})


def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("store:home")
    else:
        form = CustomSignupForm()

    return render(request, "store/signup.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('store:home')


def generate_order_number():
    # ORD + YYYYMMDD + 4digits
    return 'ORD' + timezone.now().strftime('%Y%m%d') + f"{random.randint(0,9999):04d}"

def home(request):
    categories = Category.objects.all()
    featured = Product.objects.filter(featured=True)[:4]
    return render(request, 'store/home.html', {'categories': categories, 'featured': featured})

def products(request):
    category_slug = request.GET.get('category')
    categories = Category.objects.all()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        product_list = Product.objects.filter(category=category).order_by('-created_at')
    else:
        product_list = Product.objects.all().order_by('-created_at')
    return render(request, 'store/products.html', {'products': product_list, 'categories': categories})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # add to cart
    if request.method == 'POST' and request.POST.get('action') == 'add':
        size = request.POST.get('size') or ''
        quantity = int(request.POST.get('quantity', '1'))
        cart = request.session.get('cart', {})
        key = f"{str(product.id)}::{size}"
        entry = cart.get(key, {'id': str(product.id),'name':product.name,'price': float(product.price),'size': size,'quantity':0,'image': product.image_list()[0] if product.image_list() else ''})
        entry['quantity'] += quantity
        cart[key] = entry
        request.session['cart'] = cart
        return redirect('store:cart')
    return render(request, 'store/product_detail.html', {'product': product})

def cart_view(request):
    cart = request.session.get('cart', {})
    items = list(cart.values())
    total = sum(Decimal(str(i['price'])) * i['quantity'] for i in items) if items else Decimal('0.00')
    return render(request, 'store/cart.html', {'items': items, 'total': total})

def cart_update(request):
    # update quantities or remove
    if request.method == 'POST':
        key = request.POST.get('key')
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        if key in cart:
            if action == 'remove':
                del cart[key]
            elif action == 'set':
                qty = int(request.POST.get('quantity', '1'))
                if qty <= 0:
                    del cart[key]
                else:
                    cart[key]['quantity'] = qty
        request.session['cart'] = cart
    return redirect('store:cart')

@transaction.atomic
def checkout(request):
    cart = request.session.get('cart', {})
    items = list(cart.values())

    if not items:
        return redirect('store:products')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            request.session["checkout_data"] = {
                "name": form.cleaned_data['name'],
                "email": form.cleaned_data['email'],
                "phone": form.cleaned_data['phone'],
                "address": form.cleaned_data['address'],
                "payment_method": request.POST.get("payment_method")  # IMPORTANT
            }
            return redirect("store:payment_page")

    else:
        form = CheckoutForm()

    total = sum(Decimal(str(i['price'])) * i['quantity'] for i in items)

    return render(request, 'store/checkout.html', {
        'form': form,
        'items': items,
        'total': total
    })


def payment_page(request):
    data = request.session.get("checkout_data")
    cart = request.session.get("cart", {})

    if not data or not cart:
        return redirect("store:checkout")

    items = list(cart.values())
    total = sum(Decimal(str(i['price'])) * i['quantity'] for i in items)

    return render(request, "store/payment_page.html", {
        "billing": data,
        "items": items,
        "total": total,
        "method": data.get("payment_method", "cod"),
        "razorpay_key": settings.RAZORPAY_KEY_ID,   # ✅ THIS LINE FIXES EVERYTHING
    })


def complete_order(request):
    data = request.session.get("checkout_data")
    cart = request.session.get("cart", {})

    if not data or not cart:
        return redirect("store:checkout")

    payment_method = data.get("payment_method", "cod")

    items = list(cart.values())

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        order_number=generate_order_number(),
        customer_name=data['name'],
        customer_email=data['email'],
        customer_phone=data['phone'],
        shipping_address=data['address'],
        total_amount=sum(Decimal(str(i['price'])) * i['quantity'] for i in items),
        payment_method=payment_method,
        status="paid"
    )

    for it in items:
        product_instance = Product.objects.filter(id=it["id"]).first()

        OrderItem.objects.create(
            order=order,
            product=product_instance,  # ✔ FIX
            product_name=it["name"],
            product_price=Decimal(str(it["price"])),
            size=it.get("size", ""),
            quantity=it["quantity"],
            subtotal=Decimal(str(it["price"])) * it["quantity"]
        )

    request.session["cart"] = {}
    request.session.pop("checkout_data", None)

    return redirect(reverse("store:order_success") + f"?order={order.order_number}")


def order_success(request):
    order_number = request.GET.get('order')
    if not order_number:
        return redirect('store:home')
    return render(request, 'store/order_success.html', {'order_number': order_number})


#user dashboard views
@login_required
def user_dashboard(request):
    return render(request, 'store/user_dashboard.html')


@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/user_orders.html', {'orders': orders})

def about(request):
    return render(request, "store/about.html")

def contact(request):
    if request.method == "POST":
        first = request.POST.get("first_name")
        last = request.POST.get("last_name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        full_message = f"""
New Contact Message:

Name: {first} {last}
Email: {email}
Subject: {subject}

Message:
{message}
"""

        send_mail(
            subject=f"New Contact Form Submission: {subject}",
            message=full_message,
            from_email=settings.EMAIL_HOST_USER,   # your sending email
            recipient_list=[settings.EMAIL_HOST_USER],  # your receiving inbox
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect("store:contact")

    return render(request, "store/contact.html")

#wishlist view
@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    if created:
        messages.success(request, "Added to wishlist.")
    else:
        messages.info(request, "Already in wishlist.")

    return redirect("store:wishlist")


@login_required
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, "Removed from wishlist.")
    return redirect("store:wishlist")


@login_required
def wishlist_page(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    return render(request, "store/wishlist.html", {"items": items})

#invoice view
def download_invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    items = OrderItem.objects.filter(order=order)

    # Render HTML content
    html = render_to_string("store/invoice.html", {
        "order": order,
        "items": items,
    })

    # Create HTTP response with PDF headers
    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_number}.pdf"'

    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    # If PDF fails
    if pisa_status.err:
        return HttpResponse("Error generating invoice", status=500)

    return response

# cancel order reason view
@login_required
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Only pending/packed can be cancelled
    if order.status not in ["pending", "packed"]:
        messages.error(request, "This order cannot be cancelled.")
        return redirect("store:user_orders")

    if request.method == "POST":
        form = CancelOrderForm(request.POST)
        if form.is_valid():
            order.status = "cancelled"
            order.cancel_reason = form.cleaned_data["reason"]
            order.save()

            messages.success(request, "Order cancelled successfully.")
            return redirect("store:user_orders")
    else:
        form = CancelOrderForm()

    return render(request, "store/cancel_order.html", {
        "order": order,
        "form": form,
    })

#order tracking view
def track_order_id(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return render(request, "store/track_order_page.html", {"error": "Order not found"})

    # Delivery ETA (You can customize)
    estimated_delivery = order.created_at + timedelta(days=5)

    # Timeline steps (match your order.status)
    timeline = [
        {"title": "Order Placed",      "done": True},
        {"title": "Packed",            "done": order.status in ["packed", "shipped", "out_for_delivery", "delivered"]},
        {"title": "Shipped",           "done": order.status in ["shipped", "out_for_delivery", "delivered"]},
        {"title": "Out for Delivery",  "done": order.status in ["out_for_delivery", "delivered"]},
        {"title": "Delivered",         "done": order.status == "delivered"},
    ]

    return render(request, "store/track_order_page.html", {
        "order": order,
        "timeline": timeline,
        "eta": estimated_delivery,
    })

#profile view
@login_required
def user_profile(request):
    user = request.user
    
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("store:user_profile")
    else:
        form = ProfileForm(instance=user)

    return render(request, "store/profile.html", {"form": form})

#settings view
@login_required
def settings_page(request):
    return render(request, "store/settings.html")


#Razorpay integration views

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

@login_required
def create_razorpay_order(request):
    data = request.session.get("checkout_data")
    cart = request.session.get("cart", {})

    if not data or not cart:
        return JsonResponse({"error": "Invalid session"}, status=400)

    total = sum(
        Decimal(str(i['price'])) * i['quantity'] for i in cart.values()
    )

    amount_paise = int(total * 100)

    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    request.session["razorpay_order_id"] = razorpay_order["id"]

    return JsonResponse({
        "order_id": razorpay_order["id"],
        "amount": amount_paise,
        "key": settings.RAZORPAY_KEY_ID
    })


def create_final_order(request, payment_method):
    data = request.session["checkout_data"]
    cart = request.session["cart"]

    order = Order.objects.create(
        user=request.user,
        order_number=generate_order_number(),
        customer_name=data["name"],
        customer_email=data["email"],
        customer_phone=data["phone"],
        shipping_address=data["address"],
        total_amount=sum(
            Decimal(str(i['price'])) * i['quantity'] for i in cart.values()
        ),
        payment_method=payment_method,
        status="paid"
    )

    for it in cart.values():
        OrderItem.objects.create(
            order=order,
            product_id=it["id"],
            product_name=it["name"],
            product_price=it["price"],
            quantity=it["quantity"],
            subtotal=Decimal(str(it["price"])) * it["quantity"]
        )

    request.session.flush()


@csrf_exempt
def verify_razorpay_payment(request):
    return JsonResponse({"status": "success"})
