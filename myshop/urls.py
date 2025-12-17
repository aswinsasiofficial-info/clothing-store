from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from store import views as store_views

urlpatterns = [
    path('', include(('store.urls', 'store'), namespace='store')),

    # AUTH ROUTES (REQUIRED)
  path(
    "login/",
    auth_views.LoginView.as_view(
        template_name="store/login.html",
        redirect_authenticated_user=True
    ),
    name="login"
),


    path('logout/', store_views.logout_view, name='logout'),


    path('signup/', store_views.signup_view, name='signup'),

    path('admin/', admin.site.urls),
    path("owner/", include("owner.urls", namespace="owner")),

]
