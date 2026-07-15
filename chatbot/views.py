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
        history = data.get('history', [])  # 🆕 histórico da conversa
        
        prompt = f"""Você é um atendente virtual da loja GreatKart, um ecommerce de roupas e calçados.
        
        REGRAS:
        1. Responda APENAS perguntas relacionadas à loja.
        2. Seja educado e use no máximo 3 frases.
        3. Se já se despediram, apenas diga "Obrigado, volte sempre!".
        """
        
        messages = [{"role": "system", "content": prompt}]
        
        # Adiciona histórico
        for msg in history[-10:]:  # últimas 10 mensagens
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