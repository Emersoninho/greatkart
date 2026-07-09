from django.db import models
from category.models import Category
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count

# Create your models here.
class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True, verbose_name="Nome do Produto")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug (Link Único)")
    description = models.TextField(max_length=500, blank=True, verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    images = models.ImageField(upload_to='photos/products', verbose_name="Imagem Principal")
    stock = models.IntegerField(verbose_name="Estoque")
    is_available = models.BooleanField(default=True, verbose_name="Disponível")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Categoria")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    modified_date = models.DateTimeField(auto_now=True, verbose_name="Última Modificação")
     # Campos obrigatórios para logística (Valores padrão para não quebrar o banco)
    weight = models.DecimalField(max_digits=6, decimal_places=3, default=0.300)
    length = models.DecimalField(max_digits=6, decimal_places=2, default=16.0)
    width = models.DecimalField(max_digits=6, decimal_places=2, default=11.0)
    height = models.DecimalField(max_digits=6, decimal_places=2, default=2.0)

    shipping_class = models.CharField(max_length=50, blank=True)
    
    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name
    
    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))

        avg = 0

        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg    
    
    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))

        count = 0

        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count 

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
    
class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)    
    
# Opções traduzidas para exibição no painel administrativo
Variation_category_choice = (
    ('color', 'Cor'),
    ('size', 'Tamanho'),
)    
    
class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produto")
    variation_category = models.CharField(max_length=100, choices=Variation_category_choice, verbose_name="Tipo de Variação")
    variation_value = models.CharField(max_length=100, verbose_name="Valor da Variação")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_date = models.DateTimeField(auto_now=True, verbose_name="Data de Criação")

    objects = VariationManager()
    
    def __str__(self):
        return self.variation_value

    class Meta:
        verbose_name = 'Variação'
        verbose_name_plural = 'Variações'

class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produto")
    user = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Usuário")
    subject = models.CharField(max_length=100, blank=True, verbose_name="Assunto")
    review = models.TextField(max_length=500, blank=True, verbose_name="Avaliação")
    rating = models.FloatField(verbose_name="Nota")
    ip = models.CharField(max_length=20, blank=True, verbose_name="Endereço IP")
    status = models.BooleanField(default=True, verbose_name="Status (Visível)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = 'Avaliação e Nota'
        verbose_name_plural = 'Avaliações e Notas'

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE, verbose_name="Produto")
    image = models.ImageField(upload_to='store/products', max_length=255, verbose_name="Imagem da Galeria")

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'Imagem da Galeria'
        verbose_name_plural = 'Galeria de Fotos dos Produtos'

class Banner(models.Model):
    image = models.ImageField(upload_to='banners/', verbose_name="Imagem do Banner")
    title = models.CharField(max_length=100, blank=True, verbose_name="Título")
    subtitle = models.CharField(max_length=200, blank=True, verbose_name="Subtítulo")
    link = models.URLField(blank=True, verbose_name="Link (opcional)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Banner {self.id}"

    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'        