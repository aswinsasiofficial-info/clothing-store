from django.contrib import admin
from .models import Category, Product, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','slug')
    search_fields = ('name','slug')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product_name','product_price','size','quantity','subtotal')
    can_delete = False
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number','customer_name','total_amount','status','created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number','created_at','updated_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'stock', 'featured')
    search_fields = ('name', 'slug')
    list_filter = ('featured', 'category')

    list_per_page = 1000   # or any large number