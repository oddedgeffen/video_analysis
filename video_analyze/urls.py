"""
URL configuration for video_analyze project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
import os


# Create a template view with S3 variables
class ReactAppView(TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aws_bucket_name'] = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
        context['aws_region'] = os.environ.get('AWS_S3_REGION_NAME', 'eu-central-1')
        return context


# Redirect view for /app/ to /
def redirect_to_root(request):
    return HttpResponseRedirect('/')


urlpatterns = [
    path('', ReactAppView.as_view(), name='frontend'),  # Serve React app at root URL
    path('app/', redirect_to_root, name='app_redirect'),  # Redirect /app/ to /
    path('health/', lambda request: HttpResponse('OK'), name='health'),  # Health check at /health/
    path('test/', ReactAppView.as_view(template_name='test.html'), name='test'),
    path('admin/', admin.site.urls),
    path('api/', include('video_analyzer.urls')),
    # Catch-all: serve React app for any non-API/admin/static/media paths (e.g., /trial/:code)
    re_path(r'^(?!api/|admin/|static/|media/|health/|test/).*$ ', ReactAppView.as_view(), name='frontend_catchall'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
