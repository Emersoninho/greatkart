from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .services import calcular_frete_carrinho
from carts.models import CartItem 

@require_POST
def calculate_shipping(request):
    try:
        import json

        data = json.loads(request.body)
        cep_destino = data.get("cep_destino")

        if not cep_destino:
            return JsonResponse({"error": "CEP obrigatório"}, status=400)

        current_user = request.user

        cart_items = CartItem.objects.filter(user=current_user)

        if not cart_items.exists():
            return JsonResponse({"error": "Carrinho vazio"}, status=400)

        fretes = calcular_frete_carrinho(
            #cep_origem="50000000",
            cep_destino=cep_destino,
            cart_items=cart_items
        )

        return JsonResponse({"shipping": fretes})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)