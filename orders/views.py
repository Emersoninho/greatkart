from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import mercadopago
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from decimal import Decimal
from shipping.services import MelhorEnvioService, criar_etiqueta, comprar_etiqueta, gerar_etiqueta, consultar_etiqueta
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from coupons.models import Coupon
from .models import Notification

def payments(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('store')

    # 1. Inicializa o SDK do Mercado Pago
    # Inicializa o SDK puxando o token protegido do settings

    print(settings.MERCADOPAGO_ACCESS_TOKEN[:20])
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    #sdk = mercadopago.SDK("APP_USR-3406993664207304-062410-3382ed3ed24caebbac97c9e382032005-2120059747")

    # 2. Monta os itens do carrinho no formato que a API exige
    # 3. Como as informações detalhadas estão no carrinho/OrderProduct, criamos um item genérico com o total
    total_produtos = float(order.order_total) - float(order.shipping_cost)

    shipping_cost = float(order.shipping_cost)

    items = [
        {
            "title": f"Pedido #{order.order_number}",
            "quantity": 1,
            "unit_price": total_produtos,
            "currency_id": "BRL"
        },
        {
            "title": "Frete (Melhor Envio)",
            "quantity": 1,
            "unit_price": shipping_cost,
            "currency_id": "BRL"
        }
    ]

    # Se o e-mail do cliente for real (ex: gmail, hotmail, etc.), o Sandbox do Mercado Pago rejeita.
    # Esta linha mascara temporariamente para o seu usuário de teste apenas na chamada da API:
    buyer_email = order.email

    if settings.MERCADOPAGO_SANDBOX:
        payer_email = settings.MERCADOPAGO_TEST_EMAIL
    else:
        payer_email = buyer_email

    # Seu link atualizado do Ngrok
    ngrok_domain = settings.SITE_URL

    cpf = getattr(order, "cpf", "19100000000")

    preference_data = {
    "items": items,

    "external_reference": order.order_number,

    "notification_url": f"{ngrok_domain}/orders/webhook/",

    "payer": {
        "email": payer_email,
        "first_name": order.first_name if order.first_name else "Helena",
        "last_name": order.last_name if order.last_name else "Teste",
        "identification": {
            "type": "CPF",
            "number": cpf
        }
    },

    "payment_methods": {
        "excluded_payment_methods": [],
        "excluded_payment_types": [],
        "installments": 12
    },

    "back_urls": {
        "success": f"{ngrok_domain}/orders/order_complete/?order_number={order.order_number}",
        "failure": f"{ngrok_domain}/orders/payment_failed/",
        "pending": f"{ngrok_domain}/orders/order_complete/?order_number={order.order_number}"
    },

    "auto_return": "approved",
}

    # 4. Cria a preferência nos servidores do Mercado Pago
    preference_response = sdk.preference().create(preference_data)
    print("=" * 60)
    print("STATUS DA API:", preference_response["status"])
    print("RESPOSTA DA API:")
    print(preference_response["response"])
    print("=" * 60)
    preference_info = preference_response["response"]

    # --- PRINTS PARA DEBUGAR NO TERMINAL SE FALHAR ---
    print("STATUS DA API:", preference_response["status"])
    print("RESPOSTA DA API:", preference_info)
    # ---------------------------------------------------------------------

    if preference_response["status"] == 201:
        # Esse 'init_point' é o link do checkout com Pix, Boleto e Cartão prontos
        # Como deve ficar para os seus testes:
        if settings.MERCADOPAGO_SANDBOX:
            url_checkout_mercado_pago = preference_info["sandbox_init_point"]
        else:
            url_checkout_mercado_pago = preference_info["init_point"]

        id_preferencia = preference_info["id"]

        # 5. Criamos o registro inicial na sua tabela Payment como 'Pending'
        payment = Payment.objects.create(
            user=request.user,
            payment_id=id_preferencia, # Usamos o ID da preferência temporariamente até o Webhook atualizar
            payment_method="Mercado Pago (Checkout Pro)",
            amount_paid=str(order.order_total),
            status="Pending" # Aguardando pagamento
        )
        
        order.payment = payment
        order.status = 'Pending'
        order.save()

        # 6. Redireciona o cliente direto para a tela oficial de pagamentos do Mercado Pago
        return redirect(url_checkout_mercado_pago)
        
    else:
        # Se houver falha de credencial ou comunicação com a API
        return render(request, 'orders/payment_failed.html', {"erro": preference_response})

@csrf_exempt
def mercadopago_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        webhook_data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if webhook_data.get("type") != "payment":
        return HttpResponse(status=200)

    payment_id = webhook_data.get("data", {}).get("id")
    if not payment_id:
        return HttpResponse(status=200)

    try:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        payment_info = sdk.payment().get(payment_id)
        payment_response = payment_info["response"]

        print("WEBHOOK RECEBIDO - PAYMENT ID:", payment_id)

        real_status = payment_response.get("status")
        order_number = payment_response.get("external_reference")

        if real_status != "approved" or not order_number:
            return HttpResponse(status=200)

        order = Order.objects.get(order_number=order_number)

        print(f"PEDIDO ENCONTRADO: {order.order_number} - Status: {order.status}")

        if order.is_ordered:
            print("Pedido já processado anteriormente.")
            return HttpResponse(status=200)

        # Atualiza pagamento
        if order.payment:
            order.payment.status = "Approved"
            order.payment.save()

        # Incrementa uso do cupom
        if order.coupon_code:
            try:
                coupon = Coupon.objects.get(code=order.coupon_code)
                coupon.used_count += 1
                coupon.save()
            except:
                pass    

        # Status: Preparando (pagamento aprovado)
        order.status = "Preparing"

        # Itens do pedido
        order_items = OrderProduct.objects.filter(order=order)

        # ==================== PROCESSAMENTO DO MELHOR ENVIO ====================
        if not order.label_id:
            print("INICIANDO PROCESSO AUTOMÁTICO DE ETIQUETA")
            
            service = MelhorEnvioService()

            try:
                # DEBUG: Verificar se tem itens
                order_items = OrderProduct.objects.filter(order=order)
                print(f"📦 ITENS ENCONTRADOS: {order_items.count()}")

                if not order_items.exists():
                    print("⚠️ NENHUM ITEM ENCONTRADO - buscando por payment ou user...")
                    # Tenta buscar de outras formas
                    order_items = OrderProduct.objects.filter(
                        order__order_number=order.order_number
                    )
                    print(f"📦 ITENS POR ORDER NUMBER: {order_items.count()}")

                    if not order_items.exists():
                        # Última tentativa: por payment
                        order_items = OrderProduct.objects.filter(payment=order.payment)
                        print(f"📦 ITENS POR PAYMENT: {order_items.count()}")

                if not order_items.exists():
                    raise Exception("Nenhum OrderProduct encontrado para este pedido")
            
                # Lista o que encontrou
                for item in order_items:
                    print(f"  - Produto: {item.product.product_name}, Qtd: {item.quantity}, Peso: {item.product.weight}")
                

                # 1. Criar etiqueta
                resposta = service.criar_etiqueta(order, order_items)
                label_id = resposta.get("id")
                print(f"🏷️ LABEL ID: {label_id}")

                # 2. Comprar etiqueta
                checkout = service.comprar_etiqueta(label_id)

                # 3. Gerar etiqueta
                geracao = service.gerar_etiqueta(label_id)

                # 4. Baixar PDF (agora com método alternativo)
                pdf_content = service.baixar_pdf_etiqueta_alternativo(label_id)

                if pdf_content:
                    filename = f"etiqueta_{order.order_number}_{label_id[:8]}.pdf"
                    order.shipping_label_pdf.save(filename, ContentFile(pdf_content), save=False)
                    print(f"✅ PDF salvo: {filename}")
                else:
                    print("⚠️ Falha ao baixar PDF - mas etiqueta foi gerada")

                # 5 Salvar Dados da etiqueta
                order.label_id = label_id
                order.tracking_code = resposta.get("protocol", "")
                order.tracking_url = f"https://www.melhorenvio.com.br/tracking/{label_id}"
                order.label_url = f"https://sandbox.melhorenvio.com.br/painel/envios/{label_id}"  # ⬅️ Link direto pro painel
                order.shipping_cost = float(resposta.get("price", 0))
                order.shipping_days = resposta.get("delivery_max")
                # 🔔 NOTIFICAÇÕES (depois de ter todos os dados)
                create_notification(order, f'💰 Pagamento aprovado - R$ {order.order_total}')
                create_notification(order, f'🚚 Pedido enviado - {order.tracking_code}')
                # Status: A Caminho (etiqueta gerada)
                order.status = "Shipped"
                order.is_ordered = True
                order.save()

                # Reduz estoque dos produtos
                for item in order_items:
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                        print(f"📦 Estoque atualizado: {product.product_name} = {product.stock}")
                    else:
                        print(f"⚠️ Estoque insuficiente para {product.product_name}")

                print(f"✅ Pedido {order.order_number} salvo no banco!")
                print(f"   Status: {order.status} | Label: {order.label_id} | Tracking: {order.tracking_code}")
                print(f"   - Label ID: {order.label_id}")
                print(f"   - Tracking: {order.tracking_code}")
                print(f"   - PDF: {order.shipping_label_pdf}")

            except Exception as e:
                print("❌ ERRO AO PROCESSAR ETIQUETA:")
                print(f"{type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()

    except Order.DoesNotExist:
        print(f"❌ Pedido {order_number} não encontrado no banco.")
    except Exception as e:
        print("===================================")
        print("ERRO GERAL NO WEBHOOK:")
        print(type(e).__name__, ":", str(e))
        print("===================================")

    return HttpResponse(status=200)

def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)

    for cart_item in cart_items:
        if cart_item.product.stock < cart_item.quantity:
            messages.error(request, f'Estoque insuficiente para {cart_item.product.product_name}')
            return redirect('cart')

    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    # =========================
    # SUBTOTAL (DECIMAL)
    # =========================
    total = Decimal('0.00')
    quantity = 0

    for cart_item in cart_items:
        total += Decimal(str(cart_item.product.price)) * cart_item.quantity
        quantity += cart_item.quantity

    # =========================
    # FRETE (POST)
    # =========================
    shipping_method = None
    shipping_cost = Decimal('0.00')

    if request.method == 'POST':
        for k, v in request.POST.items():
            print(k, "=", v)

        form = OrderForm(request.POST)

        if form.is_valid():

            shipping_data = request.POST.get("shipping_option")

            shipping_service_id = None
            shipping_company_id = None
            shipping_method = ""
            shipping_cost = Decimal("0.00")

            if shipping_data:
                service_id, company_id, metodo, valor = shipping_data.split("|")

                shipping_service_id = int(service_id)
                shipping_company_id = int(company_id)
                shipping_method = metodo
                shipping_cost = Decimal(valor)

            # =========================
            # TOTAL FINAL (SEM TAXA)
            # =========================

            # Verifica cupom na sessão
            coupon_discount = Decimal('0.00')
            coupon_code = request.session.get('coupon_code')
            coupon_discount_type = request.session.get('coupon_discount_type')
            coupon_discount_value = Decimal(str(request.session.get('coupon_discount_value', 0)))

            if coupon_code:
                if coupon_discount_type == 'free_shipping':
                    shipping_cost = Decimal('0.00')
                    coupon_discount = Decimal('0.00')
                elif coupon_discount_type == 'percentage':
                    coupon_discount = (total * coupon_discount_value) / Decimal('100')
                elif coupon_discount_type == 'fixed':
                    coupon_discount = coupon_discount_value

            grand_total = total + shipping_cost - coupon_discount

            

            # =========================
            # CRIAR PEDIDO
            # =========================
            data = Order()
            data.user = current_user

            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.city = form.cleaned_data['city']
            data.cep = form.cleaned_data['cep']
            data.cpf = form.cleaned_data['cpf']
            data.state = form.cleaned_data['state']
            data.order_note = form.cleaned_data['order_note']

            # =========================
            # VALORES FINAIS
            # =========================
            data.order_total = grand_total
            data.tax = Decimal('0.00')  # removido (mantém campo para não quebrar banco)

            # FRETE
            data.shipping_service_id = shipping_service_id
            data.shipping_company_id = shipping_company_id
            data.shipping_method = shipping_method
            data.shipping_cost = shipping_cost

            # Cupom
            data.coupon_code = coupon_code
            data.coupon_discount = coupon_discount

            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # =========================
            # ORDER NUMBER
            # =========================
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))

            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")

            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            # =========================
            # 🆕 CRIAR OrderProduct AQUI
            # =========================
            for cart_item in cart_items:
                OrderProduct.objects.create(
                    order=data,
                    user=current_user,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    product_price=cart_item.product.price,
                    ordered=False
                )

            order = Order.objects.get(
                user=current_user,
                is_ordered=False,
                order_number=order_number
            )

            # =========================
            # CONTEXT
            # =========================
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': Decimal('0.00'),
                'grand_total': grand_total,
                'shipping_method': shipping_method,
                'shipping_cost': shipping_cost,
            }

            return render(request, 'orders/payments.html', context)

        else:
            print("ERROS DO FORM:")
            print(form.errors)

    return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

@staff_member_required
def download_label_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.shipping_label_pdf:
        response = FileResponse(
            order.shipping_label_pdf.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="etiqueta_{order.order_number}.pdf"'
        return response
    
    from django.http import HttpResponse
    return HttpResponse("PDF não encontrado", status=404)    

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)

@login_required(login_url='login')
def cancel_order_page(request, order_number):
    """Página de cancelamento com seleção de motivo"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.status not in ['Pending', 'Preparing']:
        messages.error(request, 'Este pedido não pode ser cancelado.')
        return redirect('order_detail', order_id=order_number)
    
    return render(request, 'accounts/cancel_order.html', {'order': order})


@login_required(login_url='login')
def cancel_order(request, order_number):
    """Processa o cancelamento e reembolso"""
    if request.method != 'POST':
        return redirect('order_detail', order_id=order_number)
    
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.status not in ['Pending', 'Preparing']:
        messages.error(request, 'Este pedido não pode ser cancelado.')
        return redirect('order_detail', order_id=order_number)
    
    reason = request.POST.get('reason', '')
    details = request.POST.get('details', '')
    
    # Monta motivo completo
    full_reason = reason
    if details:
        full_reason += f" - {details}"
    
    # Processa reembolso via Mercado Pago
    try:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        # Busca o payment_id real do webhook
        payment_id = order.payment.payment_id
        
        # Cria o reembolso
        refund_data = {
            "amount": float(order.order_total)
        }
        
        refund_response = sdk.payment().refund(payment_id, refund_data)
        
        if refund_response["status"] == 200 or refund_response["status"] == 201:
            order.refund_status = "Refunded"
            order.refund_id = refund_response["response"].get("id", "")
            print(f"✅ Reembolso processado: {order.refund_id}")
        else:
            order.refund_status = "Refund Failed"
            print(f"❌ Falha no reembolso: {refund_response}")
            
    except Exception as e:
        print(f"❌ Erro ao processar reembolso: {e}")
        order.refund_status = "Refund Pending"
    
    # Atualiza pedido
    order.cancellation_reason = full_reason
    order.status = 'Cancelled'
    order.save()
    
    # Devolve estoque
    order_items = OrderProduct.objects.filter(order=order)
    for item in order_items:
        product = item.product
        product.stock += item.quantity
        product.save()
    
    messages.success(request, 'Pedido cancelado! O reembolso será processado em até 24 horas.')
    return redirect('my_orders')

def create_notification(order, message):
    """Cria notificação para o admin"""
    Notification.objects.create(
        order=order,
        message=message
    )

@staff_member_required
def get_notifications(request):
    """Retorna notificações não lidas em JSON"""
    notifications = Notification.objects.filter(is_read=False).order_by('-created_at')[:10]
    
    data = []
    for n in notifications:
        data.append({
            'id': n.id,
            'order_number': n.order.order_number,
            'message': n.message,
            'time': n.created_at.strftime('%H:%M'),
        })
    
    count = Notification.objects.filter(is_read=False).count()
    
    return JsonResponse({
        'notifications': data,
        'count': count,
    })


@staff_member_required
def mark_notification_read(request, notification_id):
    """Marca notificação como lida"""
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'ok'})


@staff_member_required
def mark_all_read(request):
    """Marca todas como lidas"""
    Notification.objects.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})    