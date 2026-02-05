from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('logout/', views.logout_view, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment_page, name='payment_page'),
    path('place-order/', views.place_order, name='place_order'),
    #path('order-success/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-success/', views.order_success, name='order_success_page'),
    path('view-order/<int:t_id>/', views.order_view, name='order_view'),
    path('cancel-order/<int:pk>/', views.cancel_order, name='cancel_order'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('category/<slug:category_slug>/', views.index, name='product_list_by_category'),
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
    path('all-electronics/', views.all_electronics, name='all_electronics'),
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('all-products/', views.all_products, name='all_products'),
    
    # Django ka inbuilt login/logout
    path('login/', auth_views.LoginView.as_view(template_name='collection/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]