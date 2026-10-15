from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import Events, LoginView, RegisterView,ReservationView

# Router for the ModelViewSet (handles /events/, /events/<id>/, etc.)
router = DefaultRouter()
router.register(r'events', Events, basename='event')
router.register(r'reserve', ReservationView, basename='reserve')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),  # Includes all generated routes from the router
]