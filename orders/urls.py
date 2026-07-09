from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/<str:order_number>/', views.payments, name='payments'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('webhook/', views.mercadopago_webhook, name='mercadopago_webhook'),
    path('admin/download-label/<int:order_id>/', views.download_label_pdf, name='download_label_pdf'),
    path('my-orders/', views.my_orders, name='my_orders'),                  # 🆕
    path('cancel/<str:order_number>/', views.cancel_order_page, name='cancel_order_page'),
    path('cancel/<str:order_number>/process/', views.cancel_order, name='cancel_order'),
    path('admin/notifications/', views.get_notifications, name='get_notifications'),
    path('admin/notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('admin/notifications/read-all/', views.mark_all_read, name='mark_all_read'),
]