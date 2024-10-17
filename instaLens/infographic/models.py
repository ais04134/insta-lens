from django.db import models
from django.utils import timezone

# Create your models here.
class User(models.Model): #나의 데이터
    user_account = models.CharField(max_length=30, default='no_account', verbose_name="사용자 인스타 아이디") #나의 아이디
    created_at = models.DateTimeField(default = timezone.now, verbose_name="크롤링 시간") #크롤링 저장 시간

    def __str__(self):
        return f"{self.user_account}"
    
class Friendships(models.Model): #친구의 데이터
    insta_id = models.CharField(max_length=30, verbose_name="인스타 아이디") #친구들의 아이디
    user_account = models.ForeignKey(User, related_name='friendships', on_delete=models.CASCADE) #나의 아이디
    is_following = models.BooleanField(default=False, verbose_name="팔로잉 여부")
    is_follower = models.BooleanField(default=False, verbose_name="팔로워 여부")
    liked_count = models.IntegerField(default=0, verbose_name="좋아요 횟수")
    created_at = models.DateTimeField(default = timezone.now, verbose_name="크롤링 시간") #크롤링 저장 시간

    def __str__(self):
        return f"{self.insta_id}"
