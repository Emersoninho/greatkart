from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import requests
import json
from store.models import Product

GROQ_API_KEY = config('GROQ_API_KEY')

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        history = data.get('history', [])
        
        # Busca produtos reais do banco
        products = Product.objects.filter(is_available=True)[:20]
        product_list = "\n".join([f"- {p.product_name} - R$ {p.price}" for p in products])
        
        prompt = f"""Você é um atendente virtual da loja GreatKart, um ecommerce de roupas e calçados.

⚠️ REGRA MAIS IMPORTANTE: 
- Só diga que um produto está disponível se ele estiver na lista abaixo.
- Se perguntarem por algo que não está na lista, diga: "Infelizmente não temos esse produto no momento. Confira nossa loja!"

📦 PRODUTOS DISPONÍVEIS:
{product_list}

CORES: Branco, Preto, Azul, Verde, Vermelho
TAMANHOS: P, M, G, GG (roupas) / 37-43 (calçados)
FRETE: Sedex e PAC pelos Correios
PAGAMENTO: Cartão, Pix e Boleto via Mercado Pago
PRAZO: 3 a 10 dias úteis
TROCAS: até 7 dias após recebimento

REGRAS:
1. Responda APENAS perguntas relacionadas à loja.
2. Seja educado e use no máximo 3 frases.
3. Se já se despediram, apenas diga "Obrigado, volte sempre!"."""
        
        messages = [{"role": "system", "content": prompt}]
        
        # Adiciona histórico
        for msg in history[-10:]:
            messages.append(msg)
        
        # Adiciona mensagem atual
        messages.append({"role": "user", "content": user_message})
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "max_tokens": 200
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            reply = result['choices'][0]['message']['content']
        except:
            reply = "Desculpe, ocorreu um erro. Contate nosso WhatsApp!"
        
        return JsonResponse({'reply': reply})
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)