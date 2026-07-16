from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from django.db.models import Q

from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, JsonResponse
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct


def store(request, category_slug=None):
    categories = None
    
    # Base: todos os produtos disponíveis
    products = Product.objects.filter(is_available=True)
    
    # Filtro por categoria
    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=categories)
    
    # 🆕 Filtro por tamanho
    sizes = request.GET.getlist('size')
    min_price = request.GET.get('min_price', 0)
    max_price = request.GET.get('max_price')

    print("=" * 50)
    print("SIZES:", sizes)
    print("MIN:", min_price)
    print("MAX:", max_price)
    print("=" * 50)
    if sizes:
        products = products.filter(
            variation__variation_value__in=sizes, 
            variation__variation_category='size'
        ).distinct()
    
    # 🆕 Filtro por preço
    min_price = request.GET.get('min_price', 0)
    max_price = request.GET.get('max_price')
    if max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)
    
    # Ordenação e paginação
    products = products.order_by('id')
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    products = Product.objects.none() 
    product_count = 0

    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            # CORRIGIDO: de 'is_avaliable' para 'is_available' para não quebrar o banco
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
                is_available=True
            )
            product_count = products.count()
        else:
            products = Product.objects.all().filter(is_available=True).order_by('-created_date')
            product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        # Trocamos o .get() por .filter().first()
        # Se houver mais de uma avaliação por erro no banco, ele pega a primeira e não trava
        review_instance = ReviewRating.objects.filter(user__id=request.user.id, product__id=product_id).first()
        
        if review_instance:
            # Caso a avaliação já exista, atualiza ela
            form = ReviewForm(request.POST, instance=review_instance)
            if form.is_valid(): # É sempre boa prática validar antes de salvar
                form.save()
                messages.success(request, 'Obrigado! Sua avaliação foi atualizada com sucesso.')
            return redirect(url)
        else:
            # Caso não exista nenhuma avaliação, cria uma nova
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Obrigado! Sua avaliação foi enviada com sucesso.')
            return redirect(url)
        