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
        Account.objects.create_user(
            first_name='Admin',
            last_name='GreatKart',
            username='admin',
            email='admin@greatkart.com',
            password='Admin123@'
        )
        return HttpResponse("✅ Admin criado! Pode remover esta URL.")
    return HttpResponse("Admin já existe!")    