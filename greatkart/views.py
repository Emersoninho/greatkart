from django.shortcuts import render
from store.models import Product, ReviewRating, Banner  # 🆕 import Banner

def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('created_date')
    
    # Banners
    banners = Banner.objects.filter(is_active=True)  # 🆕
    
    # Get the reviews
    reviews = None
    for product in products:
        reviews = ReviewRating.objects.filter(product_id=product.id, status=True)

    context = {
        'products': products,
        'reviews': reviews,
        'banners': banners,  # 🆕
    }
    return render(request, 'home.html', context)

from django.http import HttpResponse

def create_admin(request):
    from accounts.models import Account
    if not Account.objects.filter(email='admin@greatkart.com').exists():
        user = Account(
            first_name='Admin',
            last_name='GreatKart',
            username='admin',
            email='admin@greatkart.com',
            is_staff=True,
            is_superuser=True,
            is_admin=True,
            is_active=True,
        )
        user.set_password('Admin123@')
        user.save()
        return HttpResponse("✅ Admin criado!")
    return HttpResponse("Admin já existe!")  