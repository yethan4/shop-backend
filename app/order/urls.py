from rest_framework.routers import DefaultRouter
from .views import CartItemViewSet, CartViewSet

app_name = 'order'

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-item', CartItemViewSet, basename='cart-item')

urlpatterns = router.urls
