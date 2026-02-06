from django.contrib import admin
from .models import Category, Product,Customer,Order,Banner

admin.site.register(Customer)
admin.site.register(Banner)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # 'name' likhte hi 'slug' apne aap ban jayega
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'slug']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'selling_price', 'stock']
    list_filter = ['category']
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Admin list mein ye columns dikhenge
    list_display = ['id', 'customer', 'product','total_amount', 'payment_status', 'status', 'current_location', 'ordered_date']
    
    # In fields ko aap directly list view se edit kar sakte hain
    list_editable = ['status', 'payment_status','current_location']
    
    # Sidebar mein filter lagane ke liye
    list_filter = ['status','payment_status', 'ordered_date']
    
    # Search karne ke liye
    search_fields = ['id', 'customer__name', 'product__name','transaction_id']

    # Detail page par fields ka order set karne ke liye
    fieldsets = (
        ('Order Info', {
            'fields': ('customer', 'product', 'quantity', 'total_amount','payment_method', 'payment_status', 'transaction_id'),
            'description': 'Payment related information tracking'
        }),
        ('Shipping & Tracking', {
            'fields': ('status', 'current_location', 'expected_delivery', 'tracking_id')
        }),
    )
