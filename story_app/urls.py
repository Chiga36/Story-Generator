from django.urls import path
from . import views

# App namespace for URL reversing
app_name = 'story_app'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    
    # Story generation workflow
    path('generate/<uuid:generation_id>/', views.story_generation_process, name='story_generation_process'),
    path('result/<uuid:generation_id>/', views.story_result, name='story_result'),
    
    # Gallery and details
    path('gallery/', views.story_gallery, name='story_gallery'),
    path('story/<uuid:generation_id>/', views.story_detail, name='story_detail'),
    
    # API endpoints
    path('api/status/<uuid:generation_id>/', views.generation_status_api, name='generation_status_api'),

    path('result/<uuid:generation_id>/', views.story_result, name='story_result'),
]
