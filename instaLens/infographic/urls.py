from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import crawled, crawling_loading, find_unfollow_list, show_liked_stats, getInput, display_users

app_name = 'infographic'

urlpatterns = [
    path('', getInput, name='input'), #유저 입력 받는 창
    path('crawled/<str:user_account>/', crawled, name='crawled'), # 크롤링 및 출력 창
    path('loading/<str:user_account>/', crawling_loading, name='crawling_loading'), # 크롤링 및 출력 창
    path('display/unfollow/<str:user_account>/', find_unfollow_list, name='find_unfollow_list'), # 언팔 출력 창
    path('display/stats/<str:user_account>/', show_liked_stats, name='show_liked_stats'), # 시각화 출력 창
    path('display/', display_users, name ='user_overview'), #데이터베이스 저장 확인
    path('unfollow-list/<str:user_account>/', find_unfollow_list, name='find_unfollow_list')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])