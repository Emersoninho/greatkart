from .models import Coupon

def coupon_form(request):
    return {'coupon_form_active': True}