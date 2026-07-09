from django.db import models
from store.models import Product, Variation
from accounts.models import Account

# Create your models here.
class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True, verbose_name="ID do Carrinho")
    date_added = models.DateField(auto_now_add=True, verbose_name="Data de Criação")

    def __str__(self):
        return self.cart_id

    class Meta:
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'
    
class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, verbose_name="Usuário")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produto")
    variations = models.ManyToManyField(Variation, blank=True, verbose_name="Variações")
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, verbose_name="Carrinho")
    quantity = models.IntegerField(verbose_name="Quantidade")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    def sub_total(self):
        return self.product.price * self.quantity

    def __unicode__(self):
        return self.product

    class Meta:
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens dos Carrinhos'