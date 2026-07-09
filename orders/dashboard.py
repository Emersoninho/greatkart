from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import Order, OrderProduct
from store.models import Product
import json

@staff_member_required
def dashboard(request):
    hoje = timezone.now()
    mes_passado = hoje - timedelta(days=30)
    
    # Total de vendas (últimos 30 dias)
    vendas_mes = Order.objects.filter(
        created_at__gte=mes_passado,
        status__in=['Preparing', 'Shipped', 'Delivered', 'Completed']
    ).aggregate(
        total=Sum('order_total'),
        count=Count('id')
    )
    
    # Pedidos por status
    pedidos_status = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    status_labels = []
    status_data = []
    status_colors = {
        'Pending': '#f59e0b',
        'Preparing': '#3b82f6',
        'Shipped': '#8b5cf6',
        'Delivered': '#10b981',
        'Completed': '#10b981',
        'Cancelled': '#ef4444',
    }
    
    for item in pedidos_status:
        status_labels.append(item['status'])
        status_data.append(item['count'])
    
    status_colors_list = [status_colors.get(s, '#6b7280') for s in status_labels]
    
    # Vendas por mês (últimos 6 meses)
    seis_meses = hoje - timedelta(days=180)
    vendas_mensais = Order.objects.filter(
        created_at__gte=seis_meses,
        status__in=['Preparing', 'Shipped', 'Delivered', 'Completed']
    ).annotate(
        mes=TruncMonth('created_at')
    ).values('mes').annotate(
        total=Sum('order_total')
    ).order_by('mes')
    
    meses_labels = []
    meses_data = []
    for v in vendas_mensais:
        meses_labels.append(v['mes'].strftime('%b/%Y'))
        meses_data.append(float(v['total'] or 0))
    
    # Produtos mais vendidos
    top_produtos = OrderProduct.objects.filter(
        order__status__in=['Preparing', 'Shipped', 'Delivered', 'Completed']
    ).values('product__product_name').annotate(
        total_qtd=Sum('quantity')
    ).order_by('-total_qtd')[:5]
    
    produtos_labels = []
    produtos_data = []
    for p in top_produtos:
        produtos_labels.append(p['product__product_name'])
        produtos_data.append(p['total_qtd'])
    
    context = {
        'vendas_mes': vendas_mes,
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'status_colors': json.dumps(status_colors_list),
        'meses_labels': json.dumps(meses_labels),
        'meses_data': json.dumps(meses_data),
        'produtos_labels': json.dumps(produtos_labels),
        'produtos_data': json.dumps(produtos_data),
        'total_pedidos': Order.objects.count(),
        'total_produtos': Product.objects.count(),
        'total_clientes': Order.objects.values('user').distinct().count(),
    }
    
    return render(request, 'admin/dashboard.html', context)