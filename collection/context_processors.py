from .models import CartItem

def cart_count_processor(request):
    if request.user.is_authenticated:
        # Ye line database se count nikaal rahi hai
        count = CartItem.objects.filter(user=request.user).count()
        return {'cart_count': count}
    return {'cart_count': 0}