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