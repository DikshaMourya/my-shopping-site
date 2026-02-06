from django.db import models
from django.contrib.auth.models import User # Django ka inbuilt User system
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. Category Model (Mobile, Fashion, Electronics etc.)
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# 2. Product Model (Asli Product ki details)

class Product(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # original_price = MRP (जो कटी हुई दिखेगी)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # selling_price = Actual Price (जिस पर ग्राहक खरीदेगा)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # पुराने Fields (अगर आप चाहें तो इन्हें हटा भी सकती हैं क्योंकि selling_price ही काफी है)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    image = models.ImageField(upload_to='products/')
    is_featured = models.BooleanField(default=False)
    stock = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def get_discount_percent(self):
        """डिस्काउंट प्रतिशत कैलकुलेट करने के लिए"""
        if self.original_price > 0 and self.original_price > self.selling_price:
            discount = ((self.original_price - self.selling_price) / self.original_price) * 100
            return int(discount)
        return 0 # अगर डिस्काउंट नहीं है या कीमत 0 है तो 0 वापस करेगा
    
# 3. Customer Model (User ki extra details ke liye)
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Login details ke liye
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# 4. Order Model (Customer aur Product ko jodne ke liye)
class Order(models.Model):
    # Status ko choices mein rakhna tracking ke liye best hota hai
    STATUS_CHOICES = [
        ('Pending', 'Order Placed'),
        ('Packed', 'Packed & Ready'),
        ('Shipped', 'On the Way (Shipped)'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    # Ye nayi field add karein
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    current_location = models.CharField(max_length=255, default="Seller Warehouse")
    expected_delivery = models.DateField(null=True, blank=True)
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    
    ordered_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Status change ka time track karne ke liye
    
    def __str__(self):
        return f"Order {self.id} - {self.status}"
    
class Banner(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='banners/')
    
    def __str__(self):
        return self.title
    
    
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.quantity * self.product.price
    
class ShippingAddress(models.Model):
    # Address Types ke liye choices
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home (All day delivery)'),
        ('work', 'Work (Delivery between 10 AM - 5 PM)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    pincode = models.CharField(max_length=10)
    locality = models.CharField(max_length=200)
    address_area_street = models.TextField() # Area and Street
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    landmark = models.CharField(max_length=200, null=True, blank=True)
    alternate_phone = models.CharField(max_length=15, null=True, blank=True)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='home')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.pincode}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Purchase time price
    
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') # Ek user ek product ko ek hi baar add kar sake

@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        # Jab naya user banega, ye automatically uska customer record bana dega
        Customer.objects.create(
            user=instance, 
            name=instance.username, 
            email=instance.email
        )
    



