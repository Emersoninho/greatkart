from django.db import models
from accounts.models import Account
from store.models import Product, Variation

class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Usuário")
    payment_id = models.CharField(max_length=100, verbose_name="ID do Pagamento")
    payment_method = models.CharField(max_length=100, verbose_name="Método de Pagamento")
    amount_paid = models.CharField(max_length=100, verbose_name="Valor Pago")
    status = models.CharField(max_length=100, verbose_name="Status")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    def __str__(self):
        return self.payment_id

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
    
class Order(models.Model):
    # Ajustado para incluir o status de espera ('Pending') de forma explícita
    STATUS = (
    ('New', 'Novo'),
    ('Pending', 'Aguardando Pagamento'),
    ('Accepted', 'Pagamento Aprovado'),
    ('Preparing', 'Preparando Pedido'),       # 🆕
    ('Shipped', 'A Caminho'),                 # 🆕
    ('Delivered', 'Entregue'),                # 🆕
    ('Completed', 'Concluído'),
    ('Cancelled', 'Cancelado'),
)

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, verbose_name="Usuário")
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Pagamento")
    order_number = models.CharField(max_length=20, verbose_name="Número do Pedido")
    first_name = models.CharField(max_length=50, verbose_name="Nome")
    last_name = models.CharField(max_length=50, verbose_name="Sobrenome")
    phone = models.CharField(max_length=15, verbose_name="Telefone")
    email = models.EmailField(max_length=50, verbose_name="E-mail")
    address_line_1 = models.CharField(max_length=50, verbose_name="Endereço Linha 1")
    address_line_2 = models.CharField(max_length=40, blank=True, verbose_name="Endereço Linha 2 (Opcional)")
    country = models.CharField(max_length=50, verbose_name="País")
    city = models.CharField(max_length=50, verbose_name="Cidade")
    cep = models.CharField(max_length=9, verbose_name="CEP")
    cpf = models.CharField(max_length=14, verbose_name="CPF", blank=True, null=True)
    state = models.CharField(max_length=50, verbose_name="Estado")
    order_note = models.CharField(max_length=100, blank=True, verbose_name="Nota do Pedido")
    order_total = models.FloatField(verbose_name="Total do Pedido")
    #tax = models.FloatField(verbose_name="Imposto")
    
    # O padrão (default) mudou para 'Pending' para nascer aguardando o webhook do gateway
    status = models.CharField(max_length=10, choices=STATUS, default='Pending', verbose_name="Status do Pedido")
    
    shipping_company = models.CharField(max_length=100, blank=True, verbose_name="Transportadora")
    shipping_service_id = models.IntegerField(null=True, blank=True, verbose_name="ID do Serviço")
    shipping_company_id = models.IntegerField(null=True, blank=True, verbose_name="ID da Transportadora")
    shipping_method = models.CharField(max_length=100, blank=True, verbose_name="Serviço")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor do Frete")
    shipping_days = models.IntegerField(null=True, blank=True, verbose_name="Prazo de Entrega")
    tracking_code = models.CharField(max_length=100,blank=True,verbose_name="Código de Rastreio")
    tracking_url = models.URLField(blank=True, verbose_name="Link de Rastreio")
    label_id = models.CharField(max_length=100, blank=True, verbose_name="ID da Etiqueta")
    label_url = models.URLField(blank=True,verbose_name="PDF da Etiqueta")

    ip = models.CharField(max_length=20, blank=True, verbose_name="Endereço IP")
    is_ordered = models.BooleanField(default=False, verbose_name="Pedido Concluído")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")    
    update_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em") 

    shipping_label_pdf = models.FileField(upload_to='etiquetas/', blank=True, null=True, verbose_name="Arquivo PDF da Etiqueta")
    label_url = models.URLField(blank=True, verbose_name="Link da Etiqueta no Painel")

    cancellation_reason = models.TextField(blank=True, verbose_name="Motivo do Cancelamento")
    refund_status = models.CharField(max_length=20, blank=True, verbose_name="Status do Reembolso")
    refund_id = models.CharField(max_length=100, blank=True, verbose_name="ID do Reembolso")

    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    def __str__(self):
        return self.first_name

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Pedido")
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Pagamento")
    user = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Usuário")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produto")
    variation = models.ManyToManyField(Variation, blank=True, verbose_name="Variações")
    quantity = models.IntegerField(verbose_name="Quantidade")
    product_price = models.FloatField(verbose_name="Preço do Produto")
    ordered = models.BooleanField(default=False, verbose_name="Pedido Confirmado")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'Produto do Pedido'
        verbose_name_plural = 'Produtos dos Pedidos'

class Notification(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Pedido")
    message = models.CharField(max_length=255, verbose_name="Mensagem")
    is_read = models.BooleanField(default=False, verbose_name="Lida")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    
    def __str__(self):
        return f"{self.order.order_number} - {self.message}"
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']        