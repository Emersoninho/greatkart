from django.contrib import admin
from .models import Coupon

class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'min_order_value', 'used_count', 'max_uses', 'is_active', 'valid_until']
    list_editable = ['is_active']
    search_fields = ['code']
    list_filter = ['discount_type', 'is_active']

admin.site.register(Coupon, CouponAdmin)