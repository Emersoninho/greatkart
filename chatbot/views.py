from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import google.generativeai as genai
import json

GEMINI_API_KEY = config('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        prompt = f"""Você é um atendente virtual da loja GreatKart, um ecommerce de roupas e calçados.

INFORMAÇÕES DA LOJA:
- Site: https://greatkart-7swi.onrender.com
- Produtos: Camisas, Camisetas, Jeans, Calçados, Jaquetas
- Frete: Sedex e PAC pelos Correios
- Pagamento: Cartão, Pix e Boleto via Mercado Pago
- Prazo de entrega: 3 a 10 dias úteis
- Trocas: até 7 dias após recebimento
- Contato: WhatsApp (81) 99999-9999

REGRAS:
1. Responda APENAS perguntas relacionadas à loja, produtos, pedidos, fretes e pagamentos.
2. Se perguntarem algo fora do contexto da loja, diga: "Só posso ajudar com dúvidas sobre a GreatKart!"
3. Seja educado, direto e use no máximo 3 frases.
4. Sempre que possível, direcione para o WhatsApp para atendimento humano.

Cliente: {user_message}
Atendente:"""
        
        response = model.generate_content(prompt)
        reply = response.text
        
        return JsonResponse({'reply': reply})
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)