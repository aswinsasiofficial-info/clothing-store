from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Order
from django.contrib.auth.decorators import login_required

# Restrict owner panel - only admin user allowed
OWNER_EMAIL = "aswinvs555@gmail.com"


def owner_only(function):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.email != OWNER_EMAIL:
            return redirect("store:home")
        return function(request, *args, **kwargs)
    return wrapper


@login_required
@owner_only
def dashboard(request):
    orders = Order.objects.all()
    total_sales = sum(o.total_amount for o in orders)
    total_orders = orders.count()
    total_customers = Order.objects.values("customer_email").distinct().count()

    recent_orders = orders.order_by("-created_at")[:5]

    return render(request, "owner/dashboard.html", {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "recent_orders": recent_orders
    })


@login_required
@owner_only
def products(request):
    all_products = Product.objects.all()
    return render(request, "owner/products.html", {"products": all_products})


@login_required
@owner_only
def add_product(request):
    if request.method == "POST":
        name = request.POST["name"]
        price = request.POST["price"]
        stock = request.POST["stock"]
        img = request.FILES.get("image")

        Product.objects.create(name=name, price=price, stock=stock, image=img)
        return redirect("owner:products")

    return render(request, "owner/add_product.html")


@login_required
@owner_only
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.name = request.POST["name"]
        product.price = request.POST["price"]
        product.stock = request.POST["stock"]

        img = request.FILES.get("image")
        if img:
            product.image = img

        product.save()
        return redirect("owner:products")

    return render(request, "owner/edit_product.html", {"product": product})


@login_required
@owner_only
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect("owner:products")


@login_required
@owner_only
def orders(request):
    all_orders = Order.objects.order_by("-created_at")
    return render(request, "owner/orders.html", {"orders": all_orders})


@login_required
@owner_only
def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.status = request.POST["status"]
        order.save()
        return redirect("owner:orders")

    return render(request, "owner/update_order.html", {"order": order})
#delete order
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from store.models import Order

def delete_order(request, order_number):
    # Only owner/admin allowed
    if not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect("owner:orders")

    order = get_object_or_404(Order, order_number=order_number)
    order.delete()

    messages.success(request, "Order deleted successfully.")
    return redirect("owner:orders")

