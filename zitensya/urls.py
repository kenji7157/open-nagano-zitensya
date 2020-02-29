from django.urls import path
from zitensya import views

app_name = 'zitensya'
urlpatterns = [
    # トップページ
    # path('', views.index, name='index'),
    # BOT用
    path('', views.callback, name='callback'),
    ]