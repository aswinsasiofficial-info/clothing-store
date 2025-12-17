from django.urls import path
from . import views

app_name = "owner"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("products/", views.products, name="products"),
    path("product/add/", views.add_product, name="add_product"),
    path("product/edit/<uuid:product_id>/", views.edit_product, name="edit_product"),
    path("product/delete/<uuid:product_id>/", views.delete_product, name="delete_product"),

    path("orders/", views.orders, name="orders"),
    path("order/update/<uuid:order_id>/", views.update_order, name="update_order"),
    path("orders/delete/<str:order_number>/", views.delete_order, name="delete_order"),

]
