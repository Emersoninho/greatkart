from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import requests
import json

GROQ_API_KEY = config('GROQ_API_KEY')

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        prompt = f"""Você é um atendente virtual da loja GreatKart, um ecommerce de roupas e calçados.

INFORMAÇÕES DA LOJA:
- Produtos: Camisas, Camisetas, Jeans, Calçados, Jaquetas
- Frete: Sedex e PAC pelos Correios
- Pagamento: Cartão, Pix e Boleto via Mercado Pago
- Prazo de entrega: 3 a 10 dias úteis
- Trocas: até 7 dias após recebimento
- Contato: WhatsApp (81) 99999-9999

REGRAS:
1. Responda APENAS perguntas relacionadas à loja.
2. Seja educado e use no máximo 3 frases.

Cliente: {user_message}
Atendente:"""
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
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