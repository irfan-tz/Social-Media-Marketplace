from django.urls import path
from .views import SimulatePaymentView

urlpatterns = [
    path('process/', SimulatePaymentView.as_view(), name='process-payment'),
]