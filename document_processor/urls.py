from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.ProcessedDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('extract-images/', views.extract_document_images, name='extract-images'),
    path('feedback/', views.submit_feedback, name='submit-feedback'),
    path('feedback/all/', views.get_all_feedback, name='get-all-feedback'),
] 