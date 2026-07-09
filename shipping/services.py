import requests
from decouple import config
from django.core.files.base import ContentFile

# Configurações
ACCESS_TOKEN = config("MELHOR_ENVIO_ACCESS_TOKEN")
SANDBOX = config("MELHOR_ENVIO_SANDBOX", cast=bool)

BASE_URL = (
    "https://sandbox.melhorenvio.com.br"
    if SANDBOX
    else "https://www.melhorenvio.com.br"
)


class MelhorEnvioService:

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SeuEcommerce (contato@seudominio.com)"
        }

    def calcular_frete(self, cep_origem, cep_destino, peso, altura, largura, comprimento, valor_seguro):
        url = f"{BASE_URL}/api/v2/me/shipment/calculate"

        payload = {
            "from": {"postal_code": cep_origem},
            "to": {"postal_code": cep_destino},
            "products": [{
                "id": "1",
                "width": float(largura),
                "height": float(altura),
                "length": float(comprimento),
                "weight": float(peso),
                "insurance_value": float(valor_seguro),
                "quantity": 1
            }]
        }

        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        validos = []
        for item in data:
            if item.get("error") or not item.get("price"):
                continue
            validos.append(item)

        return validos

    def testar_conexao(self):
        url = f"{BASE_URL}/api/v2/me/balance"
        response = requests.get(url, headers=self.headers, timeout=30)
        print("Status:", response.status_code)
        print("Resposta:", response.text)
        return response

    def criar_etiqueta(self, order, order_items):
        """
        Cria etiqueta no carrinho do Melhor Envio
        """
        url = f"{BASE_URL}/api/v2/me/cart"

        # VERIFICAÇÃO DE SEGURANÇA
        if not order_items or len(list(order_items)) == 0:
            raise Exception("order_items está vazio - impossível criar etiqueta sem produtos")

        # Monta produtos da declaração de conteúdo
        products = []
        for item in order_items:
            products.append({
                "name": str(item.product.product_name)[:100],
                "quantity": int(item.quantity),
                "unitary_value": float(item.product_price or 0)
            })

        # Calcula peso e dimensões totais
        itens_lista = list(order_items)  # materializa o queryset

        peso_total = sum(
            float(item.product.weight or 0.3) * int(item.quantity)
            for item in itens_lista
        )

        altura_lista = [float(item.product.height or 2.0) for item in itens_lista]
        largura_lista = [float(item.product.width or 11.0) for item in itens_lista]
        comprimento_lista = [float(item.product.length or 16.0) for item in itens_lista]

        if not altura_lista:
            raise Exception("Não foi possível extrair dimensões dos produtos")

        altura_total = max(altura_lista)
        largura_total = max(largura_lista)
        comprimento_total = max(comprimento_lista)

        # Garante mínimo de 0.3kg e dimensões mínimas
        peso_total = max(peso_total, 0.3)
        altura_total = max(altura_total, 2.0)
        largura_total = max(largura_total, 11.0)
        comprimento_total = max(comprimento_total, 16.0)

        print(f"📏 DIMENSÕES CALCULADAS - Peso: {peso_total}kg, A: {altura_total}cm, L: {largura_total}cm, C: {comprimento_total}cm")

        payload = {
            "service": int(order.shipping_service_id or 2),
            "from": {
                "name": "GreatKart",
                "phone": "81996791890",
                "email": "emersoneletrotecnico2013@gmail.com",
                "address": "Avenida Pacheco Leite Filho",
                "number": "143",
                "district": "Centro",
                "city": "Paldalho",
                "state_abbr": "PE",
                "postal_code": "55825000"
            },
            "to": {
                "name": order.full_name()[:50],
                "phone": str(order.phone or "00000000000")[:15],
                "email": order.email,
                "document": str(order.cpf or "").replace(".", "").replace("-", ""),
                "address": order.address_line_1 or "",
                "number": order.address_line_2 or "S/N",
                "district": "Centro",
                "city": order.city,
                "state_abbr": order.state,
                "postal_code": str(order.cep or "").replace("-", "")
            },
            "products": products,
            "volumes": [{
                "weight": round(float(peso_total), 3),
                "width": round(float(largura_total), 2),
                "height": round(float(altura_total), 2),
                "length": round(float(comprimento_total), 2)
            }],
            "options": {
                "non_commercial": True,
                "insurance_value": float(order.order_total or 0)
            }
        }

        print("📦 CRIANDO ETIQUETA - PAYLOAD:", payload)
        
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        print("STATUS:", response.status_code)
        print("RESPOSTA:", response.text)

        response.raise_for_status()
        return response.json()

    def comprar_etiqueta(self, label_id):
        """
        Finaliza a compra da etiqueta no carrinho
        """
        url = f"{BASE_URL}/api/v2/me/shipment/checkout"

        payload = {
            "orders": [label_id]
        }

        print(f"💰 COMPRANDO ETIQUETA {label_id}")
        
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        print("COMPRA STATUS:", response.status_code)
        print("COMPRA RESPOSTA:", response.text)

        response.raise_for_status()
        return response.json()

    def gerar_etiqueta(self, label_id):
        """
        Gera a etiqueta após compra
        """
        url = f"{BASE_URL}/api/v2/me/shipment/generate"

        response = requests.post(
            url,
            json={"orders": [label_id]},
            headers=self.headers,
            timeout=30
        )

        print("GERAR STATUS:", response.status_code)
        print("GERAR:", response.text)

        response.raise_for_status()
        return response.json()

    def consultar_etiqueta(self, label_id):
        """
        Consulta detalhes da etiqueta
        """
        url = f"{BASE_URL}/api/v2/me/shipment/{label_id}"

        response = requests.get(url, headers=self.headers, timeout=30)
        print("CONSULTA STATUS:", response.status_code)
        print("CONSULTA:", response.text)

        response.raise_for_status()
        return response.json()

    def baixar_pdf_etiqueta_alternativo(self, label_id):
        """
        Tenta baixar o PDF por múltiplos endpoints
        """
        headers = self.headers.copy()
        headers["Accept"] = "application/pdf, */*"
        
        # ===== MÉTODO 1: GET no /print =====
        url_print = f"{BASE_URL}/api/v2/me/shipment/{label_id}/print"
        
        try:
            response = requests.get(url_print, headers=headers, timeout=40)
            
            print("PRINT GET STATUS:", response.status_code)
            print("PRINT CONTENT-TYPE:", response.headers.get("Content-Type"))
            
            if response.status_code == 200:
                content = response.content
                
                if content.startswith(b'%PDF'):
                    print(f"✅ PDF via /print! Tamanho: {len(content)} bytes")
                    return content
                
                # Se for JSON com URL
                try:
                    data = response.json()
                    pdf_url = data.get("url")
                    if pdf_url:
                        print(f"📎 Baixando de: {pdf_url}")
                        pdf_resp = requests.get(pdf_url, timeout=40)
                        if pdf_resp.status_code == 200:
                            return pdf_resp.content
                except:
                    pass
        except Exception as e:
            print(f"⚠️ /print falhou: {e}")
        
        # ===== MÉTODO 2: GET no /pdf =====
        url_pdf = f"{BASE_URL}/api/v2/me/shipment/{label_id}/pdf"
        
        try:
            response = requests.get(url_pdf, headers=headers, params={"mode": "private"}, timeout=40)
            
            print("PDF GET STATUS:", response.status_code)
            
            if response.status_code == 200 and response.content.startswith(b'%PDF'):
                print(f"✅ PDF via /pdf! Tamanho: {len(response.content)} bytes")
                return response.content
        except Exception as e:
            print(f"⚠️ /pdf falhou: {e}")
        
        # ===== MÉTODO 3: URL pública =====
        url_public = f"https://www.melhorenvio.com.br/tracking/{label_id}/pdf"
        
        try:
            response = requests.get(url_public, headers={"Accept": "application/pdf"}, timeout=40)
            
            if response.status_code == 200 and response.content.startswith(b'%PDF'):
                print(f"✅ PDF público! Tamanho: {len(response.content)} bytes")
                return response.content
        except Exception as e:
            print(f"⚠️ URL pública falhou: {e}")
        
        print("❌ Nenhum método conseguiu baixar o PDF")
        return None

# ==============================
# FUNÇÕES DE ATALHO
# ==============================

def criar_etiqueta(order, cart_items):
    service = MelhorEnvioService()
    return service.criar_etiqueta(order, cart_items)


def comprar_etiqueta(label_id):
    service = MelhorEnvioService()
    return service.comprar_etiqueta(label_id)


def gerar_etiqueta(label_id):
    service = MelhorEnvioService()
    return service.gerar_etiqueta(label_id)


def consultar_etiqueta(label_id):
    service = MelhorEnvioService()
    return service.consultar_etiqueta(label_id)


def calcular_frete(**kwargs):
    service = MelhorEnvioService()
    return service.calcular_frete(**kwargs)


def calcular_frete_carrinho(cep_destino, cart_items):
    peso_total = sum(float(i.product.weight) * i.quantity for i in cart_items)
    altura = max(float(i.product.height or 1) for i in cart_items)
    largura = max(float(i.product.width or 1) for i in cart_items)
    comprimento = max(float(i.product.length or 1) for i in cart_items)

    service = MelhorEnvioService()

    return service.calcular_frete(
        cep_origem=config("STORE_ZIP_CODE"),
        cep_destino=cep_destino,
        peso=peso_total,
        altura=altura,
        largura=largura,
        comprimento=comprimento,
        valor_seguro=100
    )