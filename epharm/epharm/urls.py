from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from myapp.views import PaymentSuccessView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('myapp.urls')),





    # Make sure 'app' is the name of your app
]

urlpatterns+=static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
