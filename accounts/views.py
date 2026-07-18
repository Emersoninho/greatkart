from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from orders.models import Order, OrderProduct
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings 

from carts.views import _cart_id
from carts.models import Cart, CartItem

import requests

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # Xreate User Profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user-png'
            profile.save()

            # como o render não funciona com email to trocando esse codigo para o de baixo
            # User activate
            # current_site = get_current_site(request)
            # mail_subject = 'Por favor, ative a sua conta'
            # message = render_to_string('accounts/account_verification_email.html', {
            #     'user': user,
            #     'domain': current_site,
            #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            #     'token': default_token_generator.make_token(user),
            # })
            # to_email = email
            # try:
            #     send_email = EmailMessage(
            #         mail_subject, 
            #         message, 
            #         from_email=settings.DEFAULT_FROM_EMAIL, 
            #         to=[to_email]
            #     )
            #     send_email.send()
            # except:
            #     pass # Ignora erro de e-mail no Render    
            
            # # Constrói a URL usando o NAME da rota ('login') e joga os parâmetros no final
            # url_redirect = reverse('login') + f'?command=verification&email={email}'
            # return redirect(url_redirect)
        
            # Cadastro direto - redireciona pro login porque o render não funciona
            messages.success(request, 'Cadastro realizado com sucesso! Faça login para continuar.')
            return redirect('login')

    else:        
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # deffing the product variation by cart id
                    product_variation = []
                    
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # set the cart from the user to access his product variation
                    cart_item = CartItem.objects.filter(user=user)

                    ex_var_list = []
                    id = []

                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)  

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)  
                            item.quantity += 1
                            item.user = user
                            item.save() 
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass    
            auth.login(request, user)
            messages.success(request, 'Você fez login com sucesso.')
            url = request.META.get('HTTP_REFERER', '')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except Exception as e:
                print(e)
            return redirect('dashboard')
        else:
            messages.error(request, 'Credenciais de login inválidas.') 
            return redirect('login')       
    return render(request, 'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'Você finalizou a sua sessão.')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        # Decodifica o ID do usuário que veio mascarado no link (UID)
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    # Verifica se o usuário existe e se o token de segurança é válido
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True  # Ativa a conta do cliente!
        user.save()
        messages.success(request, 'Parabéns! Sua conta foi ativada com sucesso. Agora você pode fazer login.')
        return redirect('login')
    else:
        messages.error(request, 'Este link de ativação é inválido ou já expirou.')
        return redirect('register')
    
@login_required(login_url='login')    
def dashboard(request): 
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    userprofile = UserProfile.objects.get(user_id=request.user.id)
    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }   
    return render(request, 'accounts/dashboard.html', context)

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        
        # Verifica se o e-mail existe na base de dados
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            
            # Gera o link seguro (Token e UID) igual ao que fizemos na ativação da conta
            current_site = get_current_site(request)
            mail_subject = 'Redefina a sua senha'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            
            # Envia o e-mail real
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            
            # Mensagem em português mantendo a lógica de redirecionamento original
            messages.success(request, 'O e-mail de redefinição de senha foi enviado para o seu endereço.')
            return redirect('login')
        else:
            messages.error(request, 'Esta conta de e-mail não existe!')
            return redirect('forgotPassword')
            
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        # Decodifica o ID do utilizador para verificar se é válido
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    # Se o utilizador existir e o token for válido...
    if user is not None and default_token_generator.check_token(user, token):
        # Guarda o ID do utilizador na sessão temporariamente para saber quem vai mudar a senha
        request.session['uid'] = uid
        messages.success(request, 'Por favor, introduza a sua nova senha.')
        return redirect('resetPassword')
    else:
        messages.error(request, 'Este link de ativação expirou ou é inválido.')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            # Recupera o ID do utilizador que guardámos na sessão na view anterior
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            
            # Altera a senha usando o set_password (para encriptar em hash no Django)
            user.set_password(password)
            user.save()
            
            messages.success(request, 'Senha redefinida com sucesso! Já pode fazer login.')
            return redirect('login')
        else:
            messages.error(request, 'As senhas introduzidas não coincidem!')
            return redirect('resetPassword')
            
    return render(request, 'accounts/resetPassword.html')  

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)  

@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        # 1. VERIFICAÇÃO EXTRA: Impede que a nova senha seja igual à atual
        if current_password == new_password:
            messages.error(request, 'A nova senha não pode ser igual à senha atual!')
            return redirect('change_password')

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                
                # 2. DICA DE OURO: Atualiza a sessão do usuário
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                
                messages.success(request, 'Sua senha foi atualizada com sucesso.')
                return redirect('change_password')
            else:
                messages.error(request, 'Por favor, insira a sua senha atual correta.')
                return redirect('change_password')
        else:
            messages.error(request, 'As novas senhas digitadas não coincidem!')
            return redirect('change_password')
            
    return render(request, 'accounts/change_password.html')

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