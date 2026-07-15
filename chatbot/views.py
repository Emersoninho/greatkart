from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import requests
import json

GEMINI_API_KEY = config('GEMINI_API_KEY')

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        prompt = f"""Você é um atendente virtual da loja GreatKart.

Cliente: {user_message}
Atendente:"""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            response = requests.post(url, json=payload)
            result = response.json()
            
            print("RESPOSTA GEMINI:", json.dumps(result, indent=2))
            
            # Verifica se tem candidates
            if 'candidates' in result:
                reply = result['candidates'][0]['content']['parts'][0]['text']
            elif 'error' in result:
                reply = f"Erro: {result['error']['message']}"
            else:
                reply = "Desculpe, não consegui processar sua pergunta. Tente novamente!"
                
        except Exception as e:
            reply = "Desculpe, ocorreu um erro. Entre em contato pelo WhatsApp!"
            print("ERRO:", str(e))
        
        return JsonResponse({'reply': reply})
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)