#PPPP   V   V  K   K
#P   P  V   V  K  K 
#PPPP   V   V  KKK  
#P      V   V  K  K 
#P       VVV   K   K

#Parsing all photos on a person's page vk

#Creator: Moronlll
#version: 2.5


#--import libraries/загружаем библиотеки--
import requests
import os
import time
import re
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from io import BytesIO

#--Set colors/Установка цветов--
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

#--ASCII logo/ASCII лого--
ascii_art = f"""
{GREEN}PPPP{RESET}    {BLUE}V{RESET}   {BLUE}V{RESET}   {BLUE}K{RESET}   {BLUE}K{RESET}
{GREEN}P   P{RESET}   {BLUE}V{RESET}   {BLUE}V{RESET}   {BLUE}K{RESET}  {BLUE}K{RESET}
{GREEN}PPPP{RESET}    {BLUE}V{RESET}   {BLUE}V{RESET}   {BLUE}KKK{RESET}
{GREEN}P{RESET}       {BLUE}V{RESET} {BLUE}V{RESET}     {BLUE}K{RESET}  {BLUE}K{RESET}
{GREEN}P{RESET}        {BLUE}V{RESET}      {BLUE}K{RESET}   {BLUE}K{RESET}

{GREEN}By Moronlll{RESET} 
{BLUE}version:2.5{RESET} 
"""

#--set version VK API/назначяем версию VK API--
version = '5.131'

#--print ASCII logo/вывод ASCII лого--
print(ascii_art)

#--Language selection/Выбор языка--
while True:
    lang = input("Choose language/Выберите язык (en/ru):").strip().lower()
    if lang == "":  
        lang = "en"
        break
    if lang in ['en', 'ru']:
        break
    else:
        print(f"{RED}Invalid choice! Please enter 'en' or 'ru'.{RESET}")
        print(f"{RED}Неверный выбор! Введите 'en' или 'ru'.{RESET}")

#--Mode selection/Выбор режима--
while True:
    if lang == "en":

        print(f"\n{YELLOW}ATTENTION{RESET}")
        print(f"{YELLOW}To use the program, you will need a VK access token so we can verify your identity.{RESET}")
        print(f"{YELLOW}https://id.vk.com/about/business/go/docs/ru/vkid/latest/vk-id/connection/tokens/access-token{RESET}\n")

        mode = input("Choose mode:\n1 - One-user-download\n2 - Multiple-users-download\n> ").strip()

    if lang == "ru":

        print(f"\n{YELLOW}ВНИМАНИЕ{RESET}")
        print(f"{YELLOW}Для использования программы вам потребуется vk acces token чтобы мы могли удостоверится в вашей личности.{RESET}")
        print(f"{YELLOW}https://id.vk.com/about/business/go/docs/ru/vkid/latest/vk-id/connection/tokens/access-token{RESET}\n")

        mode = input("Выберите режим:\n1 - Загрузка-одного-пользователя\n2 - Загрузка-нескольких-пользователей\n> ").strip()
    
    if mode in ['1', '2']:
        break
    if lang == "en":
        print(f"{RED}Invalid choice! Please enter '1' or '2'.{RESET}")
    if lang == "ru":
       print(f"{RED}Неверный выбор! Введите '1' или '2'.{RESET}")

#--Messages dictionary/Словарь сообщений--
messages = {
    'en': {
        'enter_user_id': "Enter VK user ID (example: 4225252): ",
        'enter_token': "Enter VK access token: ",
        'starting_download': "\n[+] Starting download for user: {}",
        'fetching_standard_albums': "\n[+] Fetching standard albums...",
        'album': " → Album: {}",
        'fetching_system_albums': "\n[+] Fetching system albums...",
        'fetching_wall_photos': "\n[+] Fetching wall post photos...",
        'all_done': f"{GREEN}\nAll photos downloaded successfully!{RESET}",
        'some_failed': f"{YELLOW}\nDownload completed, but some photos failed.{RESET}",
        'none_downloaded': f"{RED}\nNo photos were downloaded.{RESET}",
        'vk_api_error': "[VK API Error] {}",
        'request_error': "[Request Error] {}",
        'download_error': "[Download Error] {}: {}"
    },
    'ru': {
        'enter_user_id': "Введите ID пользователя VK (пример: 4225252): ",
        'enter_token': "Введите access token VK: ",
        'starting_download': "\n[+] Начинаем загрузку для пользователя: {}",
        'fetching_standard_albums': "\n[+] Получаем стандартные альбомы...",
        'album': " → Альбом: {}",
        'fetching_system_albums': "\n[+] Получаем системные альбомы...",
        'fetching_wall_photos': "\n[+] Получаем фото со стены...",
        'all_done': f"{GREEN}\nВсе фото успешно загружены!{RESET}",
        'some_failed': f"{YELLOW}\nЗагрузка завершена, но некоторые фото не удалось скачать.{RESET}",
        'none_downloaded': f"{RED}\nНи одно фото не было скачано.{RESET}",
        'vk_api_error': "[Ошибка VK API] {}",
        'request_error': "[Ошибка запроса] {}",
        'download_error': "[Ошибка скачивания] {}: {}"
    }
}

#--General functions/Главные функции--

#--User id seeker/Поиск user id--
def resolve_user_id(user_input):
    user_input = user_input.strip()

    user_input = user_input.replace("https://vk.com/", "")
    user_input = user_input.replace("http://vk.com/", "")
    user_input = user_input.replace("vk.com/", "")

    if user_input.startswith("@"):
        user_input = user_input[1:]

    if user_input.isdigit():
        return user_input

    response = vk_api_request('users.get', {'user_ids': user_input})
    if response and len(response) > 0:
        return str(response[0]['id'])

    print(messages[lang]['vk_api_error'].format("Invalid username or user not found"))
    return None

def vk_api_request(method, params):
    # Perform VK API request with error handling
    # Выполняем запрос к VK API с обработкой ошибок
    url = f"https://api.vk.com/method/{method}"
    params.update({'access_token': access_token, 'v': version})
    try:
        response = requests.get(url, params=params).json()
        if 'error' in response:
            error_msg = response['error']['error_msg']
            print(messages[lang]['vk_api_error'].format(error_msg))
            log_error(f"VK API Error for method {method}: {error_msg}")
            return None
        return response['response']
    except Exception as e:
        print(messages[lang]['request_error'].format(e))
        log_error(f"Request exception for method {method}: {e}")
        return None



#--input result/итог ввода--
if mode == '1':
    user_input = input(messages[lang]['enter_user_id']).strip()
    user_id = resolve_user_id(user_input)
    if not user_id:
        exit()

    access_token = input(messages[lang]['enter_token']).strip()

if mode == '2':
    access_token = input(messages[lang]['enter_token']).strip()

    user_ids = []

    if lang == "en":
        print("\nEnter VK user IDs one per line.")
        print("Press Enter without typing anything to finish.\n")
    else:
        print("\nВведите ID пользователей VK по одному в строке.")
        print("Чтобы закончить — нажмите Enter на пустой строке.\n")

    while True:
        uid = input("VK user ID: ").strip()

        if uid == "":
            break

        resolved = resolve_user_id(uid)
        if resolved:
            user_ids.append(resolved)
        else:
            if lang == "en":
                print(f"{RED}User not found or invalid input!{RESET}")
            else:
                print(f"{RED}Пользователь не найден или неверный ввод!{RESET}")

    if not user_ids:
        print("No users entered. Exiting...")
        exit()

#--Create one folder for grouping/Создаем одну папку для группировки--
if mode == '2':
    os.makedirs("parser_VK", exist_ok=True)
    random_folder = os.path.join(
        "parser_VK",
        f"session_{random.randint(100000, 999999999)}"
    )
    os.makedirs(random_folder, exist_ok=True)



#--Write Logs/Записываем логи--
def log_error(message):
    os.makedirs("logs", exist_ok=True)
    with open("logs/logs.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

#--Helpers/Вспомогательные функции--
def clean_filename(name):
    # Clean file/folder names from invalid characters
    # Очищаем имя файла/папки от недопустимых символов
    return re.sub(r'[\\/:"*?<>|]+', '_', name)

def get_user_name(user_id):
    # Get user's full name from VK
    # Получаем имя и фамилию пользователя из VK
    response = vk_api_request('users.get', {'user_ids': user_id})
    if response and len(response) > 0:
        user = response[0]
        full_name = f"{user.get('first_name', '')}_{user.get('last_name', '')}"
        return clean_filename(full_name)
    return str(user_id)

def download_photo(url, folder, filename, retries=3):
    # Download photo and save to folder
    # Скачиваем фото и сохраняем в папку
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, clean_filename(filename))
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                raise Exception(f"Bad status code: {response.status_code}")
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type:
                raise Exception("Response is not an image")
            if len(response.content) < 5000:
                raise Exception("File too small, possibly corrupted")
            img = Image.open(BytesIO(response.content))
            img.verify()

            with open(path, 'wb') as f:
                f.write(response.content)
            return True

        except Exception as e:
            if attempt == retries - 1:
                print(messages[lang]['download_error'].format(filename, e))
                log_error(f"Download error for {filename}: {e}")
                return False
            time.sleep(1)

#--Logic/Основная логика--
def get_albums(user_id):
    # Get user albums
    # Получаем альбомы пользователя
    response = vk_api_request('photos.getAlbums', {'owner_id': user_id})
    return response['items'] if response else []

def get_photos(owner_id, album_id):
    # Get photos from album
    # Получаем фото из альбома
    response = vk_api_request('photos.get', {
        'owner_id': owner_id,
        'album_id': album_id,
        'photo_sizes': 1,
        'count': 1000
    })
    return response['items'] if response else []

def get_wall_photos(owner_id):
    # Get photos from wall posts
    # Получаем фото из постов на стене
    photos = []
    offset = 0
    count = 100

    while True:
        response = vk_api_request('wall.get', {
            'owner_id': owner_id,
            'offset': offset,
            'count': count,
            'filter': 'owner'
        })
        if not response:
            break
        items = response.get('items', [])
        if not items:
            break
        for post in items:
            for att in post.get('attachments', []):
                if att['type'] == 'photo':
                    photos.append(att['photo'])
        if len(items) < count:
            break
        offset += count
        time.sleep(0.34)
    return photos

def process_photos(photos, folder):
    # Download all photos from list
    # Скачиваем все фото из списка
    os.makedirs(folder, exist_ok=True)
    tasks = []
    results = []
    def safe_download(url, folder, filename):
        return download_photo(url, folder, filename)
    with ThreadPoolExecutor(max_workers=5) as executor:
        for i, photo in enumerate(photos):
            sizes = photo.get('sizes', [])
            if not sizes:
                continue
            largest = sorted(
                sizes,
                key=lambda s: s['width'] * s['height']
            )[-1]
            url = largest['url']
            filename = f"{i+1}.jpg"
            tasks.append(
                executor.submit(safe_download, url, folder, filename)
            )
        for future in tqdm(
            as_completed(tasks),
            total=len(tasks),
            desc=f"Downloading → {folder}"
        ):
            results.append(future.result())
    return results.count(True)


#--Main execution/Основной запуск--
def download_user(user_id, base_root="parser_VK"):
    user_name_folder = get_user_name(user_id)
    base_folder = os.path.join(base_root, user_name_folder)


    print(messages[lang]['starting_download'].format(user_name_folder))

    total_photos_downloaded = 0
    total_photos_attempted = 0

    print(messages[lang]['fetching_standard_albums'])
    albums = get_albums(user_id)
    for album in albums:
        album_id = album['id']
        title = clean_filename(album['title'])
        print(messages[lang]['album'].format(title))
        folder_path = os.path.join(base_folder, title)
        photos = get_photos(user_id, album_id)
        total_photos_attempted += len(photos)
        total_photos_downloaded += process_photos(photos, folder_path)
        time.sleep(0.34)

    print(messages[lang]['fetching_system_albums'])
    system_albums = {
        'profile': 'Profile Photos',
        'wall': 'Wall Photos',
        'saved': 'Saved Photos'
    }

    for album_id, title in system_albums.items():
        print(messages[lang]['album'].format(title))
        folder_path = os.path.join(base_folder, clean_filename(title))
        photos = get_photos(user_id, album_id)
        total_photos_attempted += len(photos)
        total_photos_downloaded += process_photos(photos, folder_path)
        time.sleep(0.34)

    print(messages[lang]['fetching_wall_photos'])
    wall_photos = get_wall_photos(user_id)
    wall_folder = os.path.join(base_folder, "Wall_Posts")
    total_photos_attempted += len(wall_photos)
    total_photos_downloaded += process_photos(wall_photos, wall_folder)

    if total_photos_attempted == 0:
        print(messages[lang]['none_downloaded'])
    elif total_photos_downloaded < total_photos_attempted:
        print(messages[lang]['some_failed'])
    else:
        print(messages[lang]['all_done'])

if mode == '1':
    download_user(user_id)

elif mode == '2':
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(download_user, uid, random_folder)
            for uid in user_ids
        ]

        for f in as_completed(futures):
            f.result()

if lang == "en":
    input(f"\nPress Enter to exit...")
if lang == "ru":
    input(f"\nНажмите Enter для выхода...")

