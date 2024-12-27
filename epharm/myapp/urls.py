from django.conf import settings
from django.conf.urls.i18n import urlpatterns as i18n_urlpatterns
from django.urls import path
from . import views
from django.conf.urls.static import static

# Add your URLs
urlpatterns = [
    path("products/", views.product_list, name="products"),
    path('api/test/', views.test_view),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Correct static files setup

# If you need i18n URLs, you can include them like this
urlpatterns += i18n_urlpatterns
