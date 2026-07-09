from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Coupon
from decimal import Decimal

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        
        try:
            coupon = Coupon.objects.get(code=code)
            
            if not coupon.is_valid():
                messages.error(request, 'Cupom inválido ou expirado!')
                return redirect('cart')
            
            # Salva na sessão
            request.session['coupon_code'] = coupon.code
            request.session['coupon_id'] = coupon.id
            request.session['coupon_discount_type'] = coupon.discount_type
            request.session['coupon_discount_value'] = float(coupon.discount_value)
            
            if coupon.discount_type == 'free_shipping':
                messages.success(request, '🎉 Cupom aplicado! Frete grátis!')
            elif coupon.discount_type == 'percentage':
                messages.success(request, f'🎉 Cupom de {coupon.discount_value}% aplicado!')
            else:
                messages.success(request, f'🎉 Cupom de R$ {coupon.discount_value} aplicado!')
                
        except Coupon.DoesNotExist:
            messages.error(request, 'Cupom não encontrado!')
    
    return redirect('cart')


def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        del request.session['coupon_id']
        del request.session['coupon_discount_type']
        del request.session['coupon_discount_value']
        messages.success(request, 'Cupom removido!')
    
    return redirect('cart')