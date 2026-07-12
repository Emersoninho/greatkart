from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.
class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('O usuário deve ter um endereço de e-mail')
        
        if not username:
            raise ValueError('O usuário deve ter um nome de usuário')
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, first_name, last_name, email, username, password):
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

class Account(AbstractBaseUser):
    first_name = models.CharField(max_length=50, verbose_name="Nome")
    last_name = models.CharField(max_length=50, verbose_name="Sobrenome")
    username = models.CharField(max_length=50, unique=True, verbose_name="Nome de Usuário")
    email = models.EmailField(max_length=100, unique=True, verbose_name="Endereço de E-mail")
    phone_number = models.CharField(max_length=50, verbose_name="Número de Telefone")

    #required
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    last_login = models.DateTimeField(auto_now_add=True, verbose_name="Último Login")
    is_admin = models.BooleanField(default=False, verbose_name="É Administrador")
    is_staff = models.BooleanField(default=False, verbose_name="Equipe (Staff)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    is_superadmin = models.BooleanField(default=False, verbose_name="Super Administrador")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, add_label):
        return True

    class Meta:
        verbose_name = 'Conta de Usuário'
        verbose_name_plural = 'Contas de Usuários'
    
class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, verbose_name="Usuário")
    address_line_1 = models.CharField(blank=True, max_length=100, verbose_name="Endereço Linha 1")
    address_line_2 = models.CharField(blank=True, max_length=100, verbose_name="Endereço Linha 2 (Opcional)")
    profile_picture = models.ImageField(blank=True, upload_to='userprofile', verbose_name="Foto de Perfil")
    city = models.CharField(blank=True, max_length=20, verbose_name="Cidade")
    state = models.CharField(blank=True, max_length=20, verbose_name="Estado")
    country = models.CharField(blank=True, max_length=20, verbose_name="País")

    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'