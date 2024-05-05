from .views import main , frame_the_video , return_title , messages , favicon

from django.urls import path

urlpatterns = [
    
    path('', main),
    path('watch/', frame_the_video),
    path('title/', return_title),   
    path('messages', messages),
    path('favicon.ico', favicon),
]
