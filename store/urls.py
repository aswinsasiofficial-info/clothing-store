from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
app_name = 'store'

urlpatterns = [
    path("signup/",views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('dashboard/orders/', views.user_orders, name='user_orders'),
    path('payment/', views.payment_page, name='payment_page'),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("wishlist/", views.wishlist_page, name="wishlist"),
    path("wishlist/add/<int:product_id>/", views.wishlist_add, name="wishlist_add"),
    path("wishlist/remove/<uuid:product_id>/", views.wishlist_remove, name="wishlist_remove"),
    path("wishlist/add/<uuid:product_id>/", views.wishlist_add, name="wishlist_add"),
    path("invoice/<str:order_number>/", views.download_invoice, name="download_invoice"),
    path("track/<str:order_number>/", views.track_order_id, name="track_order_id"),
    path("dashboard/profile/", views.user_profile, name="user_profile"),
    path("dashboard/settings/", views.settings_page, name="settings_page"),
    path('complete-order/',views.complete_order, name='complete_order'),
    path("razorpay/create/", views.create_razorpay_order, name="razorpay_create"),
    path("razorpay/verify/", views.verify_razorpay_payment, name="razorpay_verify"),
    #cancel order
    path("order/cancel/<str:order_number>/",views.cancel_order,name="cancel_order"),
    #cancel reason
    path("order/<str:order_number>/cancel/", views.cancel_order, name="cancel_order"),



# Password Change
    path("dashboard/change-password/", 
     auth_views.PasswordChangeView.as_view(
         template_name="store/change_password.html",
         success_url="/dashboard/settings/"
     ),
     name="change_password"),
]
