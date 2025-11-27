from rest_framework.routers import DefaultRouter
from .views import CartItemViewSet, CartViewSet, OrderViewSet

app_name = 'order'

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-item', CartItemViewSet, basename='cart-item')
router.register(r'order', OrderViewSet, basename='order')

urlpatterns = router.urls
