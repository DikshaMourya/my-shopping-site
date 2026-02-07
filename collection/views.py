from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from decimal import Decimal
from .models import Product, Category, Customer, Order,Banner,CartItem, ShippingAddress,OrderItem,Wishlist
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Product, CartItem
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, F
from django.db.models import Q
import os

def index(request, category_slug=None):
    categories = Category.objects.filter(parent=None)
    customers = Customer.objects.all()
    orders = Order.objects.all()
    banners = Banner.objects.all()
    selected_category = None
    sub_categories = []
    products = Product.objects.all()
    
    user_wishlist_ids = []
    if request.user.is_authenticated:
        user_wishlist_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        
        # --- ADDED: OFFER ZONE LOGIC ---
        # अगर कैटेगरी का नाम Offer Zone है, तो केवल डिस्काउंट वाले प्रोडक्ट्स दिखाएँ
        if selected_category.name == "Offer Zone":
            products = Product.objects.filter(selling_price__lt=F('original_price'))
            sub_categories = [] # Offer zone में सब-कैटेगरी की ज़रूरत नहीं
        else:
            sub_categories = selected_category.children.all()
            if sub_categories.exists():
                products = Product.objects.filter(category__in=sub_categories) | Product.objects.filter(category=selected_category)
            else:
                products = Product.objects.filter(category=selected_category)
        # -------------------------------
            
    # --- SEARCH LOGIC (FIXED) ---
    search_query = None

    # 1. Check for Text Search in both POST and GET
    if request.POST.get('search'):
        search_query = request.POST.get('search')
    elif request.GET.get('search'):
        search_query = request.GET.get('search')

    # 2. IMAGE SEARCH (POST Request)
    if request.method == 'POST' and request.FILES.get('camera_image'):
        uploaded_file = request.FILES['camera_image']
        search_query = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ')

    # Apply search filter if query exists
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(category__name__icontains=search_query) |
            Q(category__parent__name__icontains=search_query)
        ).distinct()
        
    # --- PRICE FILTER ---
    price_filter = request.GET.get('price')
    if price_filter:
        if price_filter == 'under500':
            products = products.filter(selling_price__lt=500)
        elif price_filter == '500-2000':
            products = products.filter(selling_price__gte=500, selling_price__lte=2000)
        elif price_filter == 'above2000':
            products = products.filter(selling_price__gt=2000)

    recent_order = request.session.get('recent_order_id')
    
    context = {
        'products': products.distinct(),      
        'categories': categories,  
        'customers': customers,    
        'orders': orders,
        'banners': banners,
        'recent_order': recent_order,
        'selected_category': selected_category,
        'sub_categories': sub_categories,  
        'user_wishlist_ids': list(user_wishlist_ids),    
        'search_query': search_query,
    }
    return render(request, 'collection/index.html', context)

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Account bante hi login kar do
            return redirect('index') # Home page par bhej do
    else:
        form = UserCreationForm()
    return render(request, 'collection/signup.html', {'form': form}) 

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            print(f"User {user.username} logged in successfully!") # Debugging ke liye
            return redirect('index')
        else:
            print(form.errors) # Dekhne ke liye ki kya galti hai
    else:
        form = AuthenticationForm()
    return render(request, 'collection/login.html', {'form': form})

@login_required
def add_to_cart(request, product_id):
    # 'Product' yahan Model hai, 'product' variable hai.
    # Inhe mix na karein.
    product = get_object_or_404(Product, id=product_id) 
    
    # CartItem logic
    item, created = CartItem.objects.get_or_create(
        product=product, 
        user=request.user
    )
    
    if not created:
        item.quantity += 1
        item.save()
        
    messages.success(request, "Item added to cart!")
    return redirect('view_cart')
@login_required
def buy_now(request, product_id):
    # Sirf check karein ki product valid hai
    product = get_object_or_404(Product, id=product_id)
    
    # Session mein store karein ki hum 'Buy Now' kar rahe hain
    request.session['buy_now_product_id'] = product_id
    
    # Bina cart mein add kiye seedha checkout par bhej dein
    return redirect('checkout')

@login_required
def view_cart(request):
    items = CartItem.objects.filter(user=request.user)
    
    if not items.exists():
        return render(request, 'collection/cart.html', {'items': None})


    total_mrp = sum(item.product.original_price * item.quantity for item in items)
    total_selling_price = sum(item.product.selling_price * item.quantity for item in items)
   
    discount = total_mrp - total_selling_price
    platform_fee = 7
    final_amount = total_selling_price + platform_fee
    
    context = {
        'items': items,
        'total_mrp': total_mrp,
        'total_discount': discount,
        'total_amount': final_amount,
    }
    return render(request, 'collection/cart.html', context)
    
# Quantity badhane ke liye
def increase_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.quantity += 1
    item.save()
    return redirect('view_cart')

# Quantity ghatane ke liye
def decrease_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete() # Agar 1 se kam ho toh item remove kar do
    return redirect('view_cart')

# Item remove karne ke liye
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('view_cart')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login') # Logout ke baad login page par bhej dein
@login_required
def checkout(request):
    # 1. Check karein ki URL me item_id hai ya Session me buy_now_product_id hai
    buy_now_id = request.GET.get('item_id') or request.session.get('buy_now_product_id')
    
    items = []
    total_mrp = 0
    total_amount = 0

    if buy_now_id:
        # --- BUY NOW CASE (Sirf ek item ke liye) ---
        product = get_object_or_404(Product, id=buy_now_id)
        
        # Ek "Fake" list banayein taaki template ka loop chale
        items = [{
            'product': product,
            'quantity': 1,
            'total_price': product.selling_price
        }]
        
        # Yahan sirf isi ek product ki price count hogi
        total_mrp = product.price
        total_amount = product.selling_price
        count = 1
        
    else:
        # --- FULL CART CASE ---
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            messages.warning(request, "Aapka cart khali hai!")
            return redirect('view_cart')
            
        items = cart_items
        # Poore cart ki calculation
        total_mrp = sum(item.product.price * item.quantity for item in items)
        total_amount = sum(item.product.selling_price * item.quantity for item in items)
        count = cart_items.count()

    # Common Logic for Discount
    total_discount = total_mrp - total_amount

    # POST Logic (Address Saving) same rahega...
    # ... (Aapka purana POST code) ...

    context = {
        'items': items,
        'total_mrp': total_mrp,
        'total_amount': total_amount,
        'total_discount': total_discount,
        'count': count,
        'item_id': buy_now_id,
    }
    return render(request, 'collection/checkout.html', context)

def update_cart(request):
    quantity = int(request.GET.get('qty', 1))
    actual_unit_price = 6999
    discounted_unit_price = 4049
    delivery_charges = 40

    # Nayi calculations
    total_actual = actual_unit_price * quantity
    total_discounted = discounted_unit_price * quantity
    total_discount = total_actual - total_discounted
    final_amount = total_discounted + delivery_charges

    return JsonResponse({
        'total_actual': total_actual,
        'total_discount': total_discount,
        'final_amount': final_amount,
        'quantity': quantity
    })

@login_required
def payment_page(request):
    items = CartItem.objects.filter(user=request.user)
    if not items.exists():
        return redirect('index')
        
    actual_price = sum(item.product.price * item.quantity for item in items)
    total_amount = actual_price + 7  # Platform fee
    
    return render(request, 'collection/payment.html', {
        'total_amount': total_amount,
        'items_count': items.count()
    })
def calculate_total(cart_items):
    total = 0
    for item in cart_items:
        total += item.product.selling_price * item.quantity
    
    # Extra charges (packaging fee) agar hai toh add karein
    packaging_fee = 7 
    return total + packaging_fee

@login_required
def place_order(request):
    if request.method == 'POST':
        # 1. HTML Form se data nikaalna (Jo aapne name="address" etc diya hai)
        f_name = request.POST.get('name')
        f_phone = request.POST.get('phone')
        f_pincode = request.POST.get('pincode')
        f_address = request.POST.get('address')
        f_locality = request.POST.get('locality')
        f_city = request.POST.get('city')
        f_state = request.POST.get('state')

        # Pura address ek sath jodein
        full_address_string = f"{f_address}, {f_locality}, {f_city}, {f_state}"

        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return redirect('view_cart')

        # 2. Customer profile update karein (Taaki '0' hat jaye)
        customer, created = Customer.objects.get_or_create(user=request.user)
        customer.address = request.POST.get('address')
        customer.pincode = request.POST.get('pincode')
        customer.phone = request.POST.get('phone')
        customer.save()

        # 3. Order save karein
        for item in cart_items:
            Order.objects.create(
                customer=customer,
                product=item.product,
                quantity=item.quantity,
                total_amount=(item.product.selling_price * item.quantity) + 7,
                status='Pending'
            )
        
        # 4. Cart khali karein
        cart_items.delete()
        
        return redirect('order_success_page')

    return redirect('checkout')
    
def order_success(request):
    # Agar aap count dikhana chahte hain toh yahan se bhejna hoga
    # Filhal hum zero ya koi fixed value bhej dete hain error hatane ke liye
    recent_order_id = "MM1000789"  # Yahan aapki actual logic aayegi

    # --- STEP: Session mein order ID save karein ---
    request.session['recent_order_id'] = recent_order_id
    request.session.modified = True
    context = {
        'items_count': 0,
        'order_id': recent_order_id  # Success page par dikhane ke liye
    }
    return render(request, 'collection/success.html', context)

@login_required
def my_orders(request):
    """
    Login kiye hue user ke orders ko dikhane ke liye merged aur clean function.
    """
    # 1. Filter: Order table mein jayenge, wahan se Customer aur phir User tak pahunchenge
    # Isse sirf wahi orders dikhenge jo is logged-in user ne kiye hain.
    orders = Order.objects.filter(customer__user=request.user).order_by('-ordered_date')
    
    # 2. Context: Template ko data bhej rahe hain
    context = {
        'orders': orders
    }
    
    # 3. Render: Sahi path par return kar rahe hain
    return render(request, 'collection/my_orders.html', context)

@login_required
def order_view(request, t_id):
    order = get_object_or_404(Order, id=t_id, customer__user=request.user)
    address = ShippingAddress.objects.filter(user=request.user).last()
    
    # Agar selling_price 0 hai, toh default 'price' field uthao
    product_price = order.product.selling_price
    if product_price == 0:
        product_price = order.product.price

    subtotal = product_price * order.quantity
    total_amount = subtotal + 7 # Platform fee
    
    context = {
        'order': order,
        'address': address,
        'subtotal': subtotal,
        'total_amount': total_amount,
        'product_price': product_price, # Template mein use karne ke liye
    }
    return render(request, 'collection/order_view.html', context)

def cancel_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    if order.status == 'Pending':
        order.status = 'Cancelled'
        order.save()
    return redirect('order_view', t_id=order.id) 

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Discount calculation logic
    discount = 0
    if product.original_price > 0:
        discount = int(((product.original_price - product.selling_price) / product.original_price) * 100)
    
    return render(request, 'collection/product_detail.html', {
        'product': product,
        'discount': discount
    })
    
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
        'platform_fee': 7.00, # Jo aapne UI mein fix rakha hai
    }
    return render(request, 'collection/invoice_template.html', context)

def all_electronics(request):
    # 'Electronics' category ke saare products filter karein
    electronics_products = Product.objects.filter(category='Electronics') 
    return render(request, 'collection/all_electronics.html', {
        'products': electronics_products
    })
    
@login_required
def toggle_wishlist(request):
    product_id = request.GET.get('id')
    
    # Try-Except ki jagah get_object_or_404 use karein 
    # taaki galat ID aane par server 500 error na de
    product = get_object_or_404(Product, id=product_id)
    
    # Check karein ki kya user ne pehle se add kiya hai
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        # Agar item pehle se tha, toh remove kar do
        wishlist_item.delete()
        status = "removed"
    else:
        # Agar item naya add hua hai
        status = "added"
        
    return JsonResponse({
        'status': status,
        'product_name': product.name # Extra info frontend ke liye
    })
    
@login_required
def view_wishlist(request):
    # Sirf us user ki wishlist ke items fetch karein
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'collection/wishlist.html', {'wishlist_items': items})

def all_products(request):
    products = Product.objects.all().order_by('-created_at')
    # Agar aapne cart_count context processor banaya hai, to yahan count pass karne ki jarurat nahi hai
    return render(request, 'collection/all_products.html', {'products': products})

def offer_zone_view(request):
    # केवल वो प्रोडक्ट्स जहाँ Selling Price, MRP से कम है
    products = Product.objects.filter(selling_price__lt=F('original_price'))
    return render(request, 'index.html', {'products': products})

def cart_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'cart_count': count}