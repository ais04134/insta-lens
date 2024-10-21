import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def get_data(username, password, user_account):
    driver = init_driver()
    insta_login(driver, username, password)

    insta_search_user(driver, user_account)
    # TODO: 검색할 계정에 있는 게시물 수 확인
    contents_num = 10 #해당 계정 게시물 수 몇 개 있는지에 따라 제한 필요

    liked_users = get_likes(driver, contents_num, user_account)
    followers = get_action(driver, user_account, "followers")
    followings = get_action(driver, user_account, "following")

    time.sleep(5)  # 확인용 대기
    driver.quit()  # 드라이버 종료

    return liked_users, followers, followings

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def insta_login(driver, username, password):
    driver.get('https://www.instagram.com/accounts/login/')
    
    # 로그인 대기
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
    username_input = driver.find_element(By.NAME, 'username')
    password_input = driver.find_element(By.NAME, 'password')
    
    # 로그인 정보 입력 및 로그인 버튼 클릭
    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)
    time.sleep(10)  # 페이지 로드 대기


# 사용자 프로필 페이지로 이동
def insta_search_user(driver, user_account):
    profile_url = f"https://www.instagram.com/{user_account}/"
    driver.get(profile_url)
    time.sleep(10)  # 프로필 로드 대기

# 팔로잉 리스트 가져오기
def get_action_xpath(action_name: str) -> str:
    """
    blabla

    :param action_name:
    :return:
    """
    return {
        "following": '//span[contains(@class, "html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs")]',
        "followers": '//span[contains(@class, "html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs")]'
    }[action_name]

def get_action(driver, target_username, action_name):
    driver.get(f'https://www.instagram.com/{target_username}/')
    time.sleep(5)

    xpath = get_action_xpath(action_name)
    # 추천 부분 확인을 위해 친구 숫자 카운트
    friend_count_element = driver.find_elements(By.XPATH, xpath)
    element = friend_count_element[2]
    if element.text.isdigit():
        friend_count = int(element.text)
        if friend_count == 0: # 팔로잉이 0이라서 버튼이 활성화되지 않는 경우 처리
            return set()
        else:
            following_button_exists = True
            try:
                following_button = driver.find_element(By.XPATH, "//a[contains(@href,'/following')]")
            except NoSuchElementException:
                following_button_exists = False

            if following_button_exists:
                following_button.click()
            else:
                return set()
    else:
        friend_count = -1

    time.sleep(5)
    following = list()
    scroll_box = driver.find_element(By.XPATH, "//div[@role='dialog']//div[@class='xyi19xy x1ccrb07 xtf3nb5 x1pc53ja x1lliihq x1iyjqo2 xs83m0k xz65tgg x1rife3k x1n2onr6']")
    last_height, height = 0, 1
    while True:
        last_height = height
        time.sleep(2)
        height = driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight; return arguments[0].scrollHeight;", scroll_box)
        links = scroll_box.find_elements(By.TAG_NAME, 'a')
        following.extend([link.text for link in links if link.text != ''])
        # 스크롤 높이가 더 이상 변하지 않으면 반복문 종료
        if last_height == height:
            scroll_attempts += 1
            if scroll_attempts >= 2: # 3번 연속 실패 시 종료
                break
        else:
            scroll_attempts = 0 # 높이가 변하면 시도 횟수 초기화


    # 팔로워 수가 20보다 적으면 중복 제거하고 friend_count만큼만 살리기
    if friend_count > 0 and friend_count <= 20:
        # 중복 제거 후 목록 반환
        unique_following = []
        for follow in following:
            if follow not in unique_following:
                unique_following.append(follow)
            if len(unique_following) == friend_count:
                break
        return set(unique_following)
    else:
        # 20 이상일 시 세트로 변환 중복 제거 후 반환
        return set(following)


# 최근 n개 게시물에서 좋아요를 한 사용자 목록 가져오기
def get_likes(driver, contents_num, username):
    #posts = driver.find_elements(By.XPATH, '//a[contains(@href, "/p/") or contains(@href, "/reels/")]')
    posts = driver.find_elements(By.XPATH, '//a[contains(@class, "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz _a6hd")]')    
    post_links = []
    for post in posts[:contents_num]:
        link = post.get_attribute('href')
        if "/p/" in link or "/reel/" in link:
            link = link.replace(username+"/", "").replace("/reel/", "/p/")
            post_links.append(link)
    
    # 사용자 아이디 수집용 dict
    like_users = dict()

    if not post_links:
        #print(f"게시글이 없습니다.")
        return like_users

    for index, post_url in enumerate(post_links, start=1):
        # 좋아요 페이지로 이동
        driver.get(f'{post_url}liked_by/')
        time.sleep(2)  # 로딩 후 대기
        try:
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # 좋아요 사용자 리스트 가져오기
                users = driver.find_elements(By.XPATH, '//span[contains(@class, "_ap3a _aaco _aacw _aacx _aad7 _aade")]')
                for user in users:
                    like_users[user.text] = like_users.get(user.text, 0) + 1
                # 스크롤 내리기
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 스크롤 후 대기
                time.sleep(1)

                # 새로운 높이 계산
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                # 마지막 높이와 비교하여 더 이상 스크롤할 수 없으면 종료
                if new_height == last_height:
                    break
                last_height = new_height

            # 좋아요 사용자 출력
            #print(f"Post {index} URL: {post_url} - Liked Users: {', '.join(list(like_users)[:len(like_users)])}")
            #print(f"Post {index} URL: {post_url} - Liked Users: {', '.join(f'{key}: {value}' for key, value in like_users.items())}")         
        except Exception as NoLikedList:
            print(f"좋아요 사용자 리스트를 찾는 데 실패했습니다: {NoLikedList}")
    return like_users

'''
# 사용자 인풋 받기
if __name__ == "__main__":
    time.sleep(5)
    instagram_username = input("인스타그램 아이디: ")
    instagram_password = input("인스타그램 비밀번호: ")
    time.sleep(10)
    target_username = input("확인하고 싶은 사용자 아이디: ")
    find_non_followers(instagram_username, instagram_password, target_username)
'''