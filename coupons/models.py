from django.db import models

class Coupon(models.Model):
    DISCOUNT_TYPE = (
        ('percentage', 'Porcentagem (%)'),
        ('fixed', 'Valor Fixo (R$)'),
        ('free_shipping', 'Frete Grátis'),
    )
    
    code = models.CharField(max_length=50, unique=True, verbose_name="Código do Cupom")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE, verbose_name="Tipo de Desconto")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor do Desconto")
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Mínimo do Pedido")
    max_uses = models.IntegerField(default=0, verbose_name="Limite de Usos (0 = ilimitado)")
    used_count = models.IntegerField(default=0, verbose_name="Usos Realizados")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    valid_from = models.DateTimeField(verbose_name="Válido de")
    valid_until = models.DateTimeField(verbose_name="Válido até")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        
        if now < self.valid_from or now > self.valid_until:
            return False
        
        return True
    
    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name = 'Cupom'
        verbose_name_plural = 'Cupons'