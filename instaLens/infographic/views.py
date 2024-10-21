import io
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from matplotlib_venn import venn2

from .insta_tracker import get_data  # 크롤러 import
from .models import User, Friendships


def getInput(request: HttpRequest) -> HttpResponse:
    message = ""
    user_account = ""
    if request.method == 'POST':
        user_account = request.POST.get('username')
        if user_account:
            return HttpResponseRedirect(reverse('infographic:crawled', args=[user_account]))
        else:
            message = "계정 이름을 입력하세요."
    return render(request, 'account_input.html', {'message': message, 'user_account':user_account})

def crawled(request: HttpRequest, user_account: str) -> HttpResponse:
    # 인스타그램 임시 로그인 아이디 정보
    username = ""
    password = ""

    failure_message = []
    '''
    liked_users(dict) - {key : friend name}, {value : 좋아요 수}
    followers(list) - friend name
    followings(list) - friend name
    '''
    try:
        liked_users, followers, followings = get_data(username, password, user_account) or ({}, {}, {})
    except Exception as e:
        failure_message.append(f"크롤링 중 오류 발생\n세부 오류 내용: {str(e)}")
        return render(request, 'crawled_result.html', {'message': failure_message})
    '''
    >> ???? models.py에 정의되어 있는거 아닌가요?
    
    DB 구조
    [User]
    - user_account (사용자 인스타 아이디)
    - created_at (크롤링 날짜)
    [Friendships]
    - insta_id (친구의 아이디)
    - user_account (Foreign - 사용자 인스타 아이디)
    - is_following (팔로잉 여부)
    - is_follower (팔로워 여부)
    - liked_count (좋아요 횟수)
    - created_at (크롤링 날짜)
    '''
    user, created = User.objects.update_or_create(
        user_account = user_account,
        defaults= {
            'created_at': timezone.now()
                  }
        )

    if liked_users:
        for insta_id, liked_count in liked_users.items():
            is_follower = insta_id in followers
            is_following = insta_id in followings
            if insta_id != user_account:
                Friendships.objects.create(
                    insta_id = insta_id,
                    user_account = user,
                    liked_count = liked_count,
                    is_follower = is_follower,
                    is_following = is_following,
                    created_at = user.created_at
                )
    else:
        failure_message.append("게시글이 없습니다. 따라서 Like Stats 내용이 없을 수 있습니다.")

    all_instas = followers.union(followings)  # followers와 followings의 모든 insta_id
    if all_instas:
        print(f"Total Insta ID to check: {len(all_instas)}")
        for insta_id in all_instas:
            is_follower = insta_id in followers
            is_following = insta_id in followings
            
            if (liked_users and insta_id not in liked_users) or (not liked_users):  # liked_users에 포함되지 않은 경우
                Friendships.objects.create(
                    insta_id = insta_id,
                    user_account = user,
                    liked_count = 0,
                    is_follower = is_follower,
                    is_following = is_following,
                    created_at = user.created_at
                )
    else:
        failure_message.append('팔로워나 팔로잉이 없습니다. Follow Tracker 나 Like Stats 내용이 없을 수 있습니다.')
    failure_message.append("크롤링이 완료되었습니다. Follow Tracker 나 Like Stats 탭을 확인해보세요")
    return render(request, 'crawled_result.html', {'message': failure_message, 'user_account': user_account})

def crawling_loading(request, user_account):
    # 크롤링 없이 랜딩 페이지 테스트 함수
    message = []
    message.append("테스트 중입니다.")
    message.append("게시글이 없습니다. 따라서 Like Stats 내용이 없을 수 있습니다.")
    message.append("팔로워나 팔로잉이 없습니다. Follow Tracker 나 Like Stats 내용이 없을 수 있습니다.")
    message.append("크롤링이 완료되었습니다. Follow Tracker 나 Like Stats 탭을 확인해보세요")
    return render(request, 'crawled_result.html', {'message': message, 'user_account': user_account})

def createDatabase(request):
    users = User.objects.all()
    friendships = Friendships.objects.all()
    users_df = pd.DataFrame(list(users.values()))
    friendships_df = pd.DataFrame(list(friendships.values()))
    data = pd.merge(friendships_df, users_df, on='user_account', how='inner')
    grouped = data.groupby('user_account').agg(list).reset_index()

# 24.10.16 건현, 상훈, 서하
def find_unfollow_list(request, user_account):
    data = request.session.get('data')  # 세션에서 data 가져오기

    try:
        # DB에서 팔로워 팔로잉 조회해서 언팔할 리스트 뽑기
        users = User.objects.all()
        friendships = Friendships.objects.all()
        users_df = pd.DataFrame(list(users.values()))
        friendships_df = pd.DataFrame(list(friendships.values()))
        # 각 데이터프레임의 컬럼명 출력
        print("Users DataFrame Columns:")
        print(users_df.columns.tolist())  # users_df의 컬럼명 리스트 출력

        print("\nFriendships DataFrame Columns:")
        print(friendships_df.columns.tolist())  # friendships_df의 컬럼명 리스트 출력
                # User와 Friendships 데이터를 병합해서 `data` 생성
        data = pd.merge(friendships_df, users_df, left_on='user_account_id', right_on='id', how='inner')
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return render(request, 'myapp/error.html', {'error': str(e)})

    plt.switch_backend('Agg')  # GUI 백엔드를 비활성화

    # 상훈님 밴 다이어그램
    following_set = set(data[(data['user_account'] == user_account) & (data['is_following'])]['insta_id'])
    follower_set = set(data[(data['user_account'] == user_account) & (data['is_follower'])]['insta_id'])
    
    venn = venn2([following_set, follower_set], 
                 set_labels=('Following', 'Follower'),
                 set_colors=('purple', 'orange')
    )
    plt.title(f'Venn Diagram of Following and Follower Status for {user_account}')
    
    # 그래프를 파일로 저장
    venn_image_path = os.path.join(settings.BASE_DIR, 'infographic/static/images/visualization', 'venn_output.png')
    plt.savefig(venn_image_path)  # 이미지 파일로 저장
    # 템플릿에 전달할 이미지 URL
    venn_plot_url = os.path.join(settings.STATIC_URL, 'images/visualization/venn_output.png')
    
    # 총 팔로잉 및 팔로워 수 시각화
    user_accounts = data.groupby('user_account').agg(
        total_following=('is_following', 'sum'),
        total_follower=('is_follower', 'sum')
    ).reset_index()

    # 막대그래프 생성
    user_accounts.set_index('user_account').plot(
        kind='bar', 
        figsize=(10, 6),
        color = ['#1f77b4', '#ff7f0e']
    )
    plt.title('Total Following and Follower Count per User Account')
    plt.xlabel('User Account')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.legend(title='Account Type', labels=['Total Following', 'Total Follower'])
    plt.tight_layout()  # 레이아웃 조정
    
    # 그래프를 파일로 저장
    bar_image_path = os.path.join(settings.BASE_DIR, 'infographic/static/images/visualization', 'bar_output.png')
    plt.savefig(bar_image_path)  # 이미지 파일로 저장
    # 템플릿에 전달할 이미지 URL
    bar_plot_url = os.path.join(settings.STATIC_URL, 'images/visualization/bar_output.png')
    
    # 언팔 목록 테이블
    unfollowed_friends = data[(data['is_following'] == True) & (data['is_follower'] == False)]
    unfollowed_friend_ids = unfollowed_friends['insta_id'].unique()

    # DataFrame으로 변환
    unfollowed_friends_df = pd.DataFrame(unfollowed_friend_ids, columns=['Unfollowed Friends'])

    n_columns = 3
    max_length = int(np.ceil(len(unfollowed_friends_df) / n_columns))
    split_data = []

    for i in range(n_columns):
        col_data = unfollowed_friends_df.iloc[i * max_length : (i + 1) * max_length].reset_index(drop=True)

        while len(col_data) < max_length:
            col_data = pd.concat([col_data, pd.DataFrame([['']], columns=['Unfollowed Friends'])], ignore_index=True)
        
        split_data.append(col_data)

    combined_df = pd.concat(split_data, axis=1)

    # 테이블 시각화
    plt.figure(figsize=(8, 4))
    plt.axis('tight')
    plt.axis('off')

    table = plt.table(cellText=combined_df.values,
                    colLabels=None,  
                    cellLoc='center', loc='center')

    # 스타일 조정
    table.auto_set_font_size(False)
    table.set_fontsize(12) 
    table.scale(1.5, 1.5)  

    # 셀 색상 설정
    for (i, j), cell in table.get_celld().items():
        cell.set_fontsize(12)  
        cell.set_facecolor('#FFFFFF')  

    # 이미지 저장
    img = io.BytesIO()  
    plt.savefig(img, format='png')  
    img.seek(0)


    # 그래프를 파일로 저장
    table_image_path = os.path.join(settings.BASE_DIR, 'infographic/static/images/visualization', 'table_output.png')
    plt.savefig(table_image_path)  # 이미지 파일로 저장
    # 템플릿에 전달할 이미지 URL
    table_plot_url = os.path.join(settings.STATIC_URL, 'images/visualization/table_output.png')


    #print(plot_url , "최종 전달 url")

# DB에서 팔로워 팔로잉 조회 해서 언팔할 리스트 뽑기
    df = pd.DataFrame(data)

    # 각 조합별로 그룹화
    groups = {
        "Not Following and Not Followed": df[(df['is_following'] == False) & (df['is_follower'] == False)],
        "Following but Not Followed": df[(df['is_following'] == True) & (df['is_follower'] == False)],
        "Not Following but Followed": df[(df['is_following'] == False) & (df['is_follower'] == True)],
        "Following and Followed": df[(df['is_following'] == True) & (df['is_follower'] == True)]
    }
    # 파이 차트를 그리기
    plt.figure(figsize=(16, 12))

    # 각 그룹에 대해 좋아요 횟수에 따른 그룹화
    for i, (label, group_data) in enumerate(groups.items()):
        if group_data.empty:
            continue  # 그룹이 비어 있으면 스킵

        # 각 사용자 계정에 대한 파이 차트를 그리기
        for j, (account, account_data) in enumerate(group_data.groupby('user_account')):
            plt.subplot(4, 3, i * 3 + j + 1)  # 4x3 서브플롯

            # 좋아요 횟수에 따른 파이 차트 그리기
            if not account_data.empty:
                likes_count = account_data['liked_count'].value_counts().sort_index()  # 좋아요 횟수에 대한 카운트
                plt.pie(
                    likes_count, labels=likes_count.index, autopct='%1.1f%%', 
                    startangle=90, colors=['#4B8BBE', '#E6B32B', '#A62D2D', '#5A8B25', '#25A0B7'],
                    explode=[0.1 if count == max(likes_count) else 0 for count in likes_count],
                    wedgeprops={'edgecolor': 'white', 'linewidth': 1}
                )
                plt.title(f'{label} {account}')  # user_account 이름 사용
            else:
                plt.axis('off')  # 그룹이 없을 경우 빈 공간으로 설정

        plt.tight_layout()

        # 그래프를 파일로 저장
        pie_chart_path = os.path.join(settings.BASE_DIR, 'infographic/static/images/visualization', 'pie_chart.png')
        
        #print(image_path , "이 경로로 나오지롱")
        plt.savefig(pie_chart_path)  # 이미지 파일로 저장
        # 템플릿에 전달할 이미지 URL
        pie_chart_url = os.path.join(settings.STATIC_URL, 'images/visualization/pie_chart.png')


    # 템플릿에 이미지 경로 전달
    return render(request, 'show_unfollow_list.html', 
                  {'user_account': user_account, 
                   'venn_plot_url': venn_plot_url, 
                   'bar_plot_url': bar_plot_url,
                   'table_plot_url' : table_plot_url,
                   'pie_chart_url': pie_chart_url})

    # if data is None:
    #     # data가 없을 경우 에러 처리
    #     return render(request, 'show_unfollow_list.html', {'message': '데이터를 찾을 수 없습니다.', 'user_account': user_account})


    # return render(request, 'show_unfollow_list.html', {'user_account': user_account})

def show_liked_stats(request, user_account):

    data = request.session.get('data')  # 세션에서 data 가져오기

    liked_following_path = os.path.join(settings.BASE_DIR, 'infographic/static/images/visualization', 'liked_following.png')
    liked_follower_path = os.path.join(settings.BASE_DIR, 'infographic/static/images/visualization', 'liked_follower.png')
    liked_count_path = os.path.join(settings.BASE_DIR, 'infographic/static/images/visualization', 'liked_following.png') 
    matplotlib.use('Agg')  # 이 코드를 추가하여 GUI 비활성화
    try:
        # DB에서 팔로워 팔로잉 조회해서 언팔할 리스트 뽑기
        users = User.objects.all()
        friendships = Friendships.objects.all()
        users_df = pd.DataFrame(list(users.values()))
        friendships_df = pd.DataFrame(list(friendships.values()))
        # 각 데이터프레임의 컬럼명 출력
        print("Users DataFrame Columns:")
        print(users_df.columns.tolist())  # users_df의 컬럼명 리스트 출력

        print("\nFriendships DataFrame Columns:")
        print(friendships_df.columns.tolist())  # friendships_df의 컬럼명 리스트 출력
                # User와 Friendships 데이터를 병합해서 `data` 생성
        data = pd.merge(friendships_df, users_df, left_on='user_account_id', right_on='id', how='inner')
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return render(request, 'myapp/error.html', {'error': str(e)})

    # 사용자로부터 user_account 입력받기
    user_account_input = user_account  # 여기에서 원하는 user_account를 직접 입력할 수 있습니다.

    # 팔로잉 중에 좋아요 눌러주는 사람, 안눌러주는 사람 파이 차트

    # 팔로잉 중에 좋아요 눌러주는 사람, 안 눌러주는 사람
    grouped_data = data.groupby(['user_account', 'is_following'])['liked_count'].sum().unstack(fill_value=0)

    # 입력받은 user_account에 대한 데이터가 있는지 확인
    if user_account_input in grouped_data.index:
        # 파이 차트 생성
        plt.figure(figsize=(8, 6))
        plt.pie(grouped_data.loc[user_account_input], labels=['Not Following', 'Following'], autopct='%1.1f%%', startangle=90, colors=['#66c2a5', '#fc8d62'])
        plt.title(f'Liked Count Distribution for {user_account_input}')
        plt.axis('equal')  # 원형으로 유지
        plt.show()
    else:
        print(f"No data found for user account: {user_account_input}")
        
    plt.savefig(liked_following_path)  # 이미지 파일로 저장
    liked_following_url = os.path.join(settings.STATIC_URL, 'images/visualization/liked_following.png')

    # 팔로워 중에 좋아요 눌러주는 사람, 안 눌러주는 사람
    grouped_data = data.groupby(['user_account', 'is_follower'])['liked_count'].sum().unstack(fill_value=0)

    # 입력받은 user_account에 대한 데이터가 있는지 확인
    if user_account_input in grouped_data.index:
        # 파이 차트 생성
        plt.figure(figsize=(8, 6))
        plt.pie(grouped_data.loc[user_account_input], labels=['Not Follower', 'Follower'], autopct='%1.1f%%', startangle=90, colors=['#b4ac6a', '#cc81a2'])
        plt.title(f'Liked Count Distribution for {user_account_input}')
        plt.axis('equal')  # 원형으로 유지
        plt.show()
    else:
        print(f"No data found for user account: {user_account_input}")

    plt.savefig(liked_follower_path) 
    liked_follower_url = os.path.join(settings.STATIC_URL, 'images/visualization/liked_follower.png')

    # # 입력받은 user_account에 해당하는 데이터 필터링
    # user_data = data[data['user_account'] == user_account_input]

    # # liked_count와 insta_id를 포함한 DataFrame 생성
    # likes_info = user_data[['insta_id', 'liked_count']]

    # # 데이터가 10명 이상이면 상위 10명을, 그렇지 않으면 전체를 보여줌
    # top_likes = likes_info.nlargest(10, 'liked_count') if len(likes_info) >= 10 else likes_info
    # print(top_likes)
#    plt.savefig(liked_count_path) 
    # 템플릿에 전달할 이미지 URL
#    liked_count_url = os.path.join(settings.STATIC_URL, 'images/visualization/liked_count.png')

    return render(request, 'show_liked_stats.html', {'message': '데이터를 찾을 수 없습니다.', 'user_account': user_account, 'liked_following_url':liked_following_url, 'liked_follower_url':liked_follower_url, #'liked_count_url':liked_count_url
                                                     })

    # 좋아요 관련 Stat 뽑기
    # 팔로잉 중에 좋아요 눌러주는 사람, 안눌러주는 사람 파이 차트
    # 팔로워 중에 좋아요 눌러주는 사람, 안눌러주는 사람 파이 차트
    # 좋아요 해주는 사람 횟수에 따른 파이 차트

def display_users(request):
    #데이터베이스에서 객체 모두 조회
    users = User.objects.all()
    friendships = Friendships.objects.all()
    print(f"Users model rows count: {User.objects.count()}")
    print(f"Friendship model rows count: {User.objects.count()}")
    #템플릿에 데이터 전달
    return render(request, 'user_overview.html', {
        'users': users,
        'friendships' : friendships
        })