import json
import requests
import time
from datetime import datetime
from tqdm import tqdm


class VkUser:

    def __init__(self, vk_token, user_id, count_photo):
        self.url = 'https://api.vk.com/method/'
        self.params = {
            'access_token': vk_token,
            'v': '5.131'
        }
        self.user_id = user_id
        self.count_photo = count_photo
        self.photos = []

    def get_photos(self, album_id=-6):
        url = self.url + 'photos.get'
        params = {
            'owner_id': self.user_id,
            'album_id': album_id,
            'count': self.count_photo,
            'rev': 1,
            'extended': 1,
            'photo_sizes': 1,
            'access_token': self.params['access_token'],
            'v': self.params['v']
        }
        response = requests.get(url, params=params)
        data = json.loads(response.text)['response']['items']
        photo_urls = {}
        for photo in tqdm(data):
            time.sleep(0.15)
            if 'likes' in photo:
                file_name = f"{photo['likes']['count']}_{datetime.fromtimestamp(photo['date']).strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            else:
                file_name = f"{datetime.fromtimestamp(photo['date']).strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            size_dict = {'s': 1, 'm': 2, 'o': 3, 'p': 4, 'q': 5, 'r': 6, 'x': 7, 'y': 8, 'z': 9, 'w': 10}
            size_max = max(photo['sizes'], key=lambda x: size_dict[x['type']])
            size = size_max['type'].upper()
            self.photos.append({'file_name': file_name, 'size': size})
            photo_urls[f"url_{len(photo_urls) + 1}"] = size_max['url']
        self.sort_photos()
        with open('photos_info.json', 'w') as f:
            json.dump(self.photos, f, ensure_ascii=False, indent=4)
        with open('photo_urls.json', 'w') as f:
            json.dump(photo_urls, f, ensure_ascii=False, indent=4)
        return photo_urls

    def sort_photos(self):
        self.photos = sorted(self.photos, key=lambda x: (x['file_name'].split('_')[0], x['file_name'].split('_')[1], x['size']))

    def save_photos_info(self, file_name='photos_info.txt'):
        with open(file_name, 'w') as f:
            for photo in tqdm(self.photos):
                time.sleep(0.10)
                f.write(f"{photo['file_name']} - {photo['date']} - {photo['size']} bytes\n")
        print(f"Photos information saved to {file_name}.")


class YaDisc:
    files_url = 'https://cloud-api.yandex.net/v1/disk/resources'

    def __init__(self):
        with open('ya_token.ini', 'r', encoding='utf-8') as file:
            self.ya_token = file.read().strip()
        self.yandex_folder = input('Введите название новой папки куда сохранить фото: ')

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.ya_token)
        }

    def create_folder(self):
        headers = self.get_headers()
        params = {"path": self.yandex_folder, "overwrite": "true"}
        response = requests.put(self.files_url, headers=headers, params=params)
        # print(response.json())
        if response.status_code == 201:
            print(f'Папка: {self.yandex_folder} успешно создана на Yandex Disk')
        elif response.status_code == 409:
            print(f"Папка {self.yandex_folder} уже существует")
        else:
            print("Ошибка при создании папки")

    def upload_file(self, photo_url, photos_info):
        headers = self.get_headers()
        url = f"{self.files_url}/upload"
        params = {"path": f"{self.yandex_folder}/{photos_info}", 'url': photo_url, "overwrite": "true"}
        response = requests.post(url=url, headers=headers, params=params)
        if response.status_code == 202:
            print(f"Файл {photos_info} успешно загружен на Яндекс.Диск")
        else:
            print(f"Не удалось загрузить файл {photos_info} на Яндекс.Диск. Код ошибки: {response.status_code}")


if __name__ == '__main__':
    with open('vk_token.ini', 'r', encoding='utf-8') as file:
        vk_token = file.read().strip()

    user_id = input('Введите ID пользователя VK: ')
    count_photo = int(input('Введите количество фото для скачивания: '))

    vk_user = VkUser(vk_token, user_id, count_photo)
    photo_urls = vk_user.get_photos()
    photos_info = json.loads(open('photos_info.json', 'r', encoding='utf-8').read())

    ya_disk = YaDisc()
    ya_disk.create_folder()

    for url, info in tqdm(zip(photo_urls.values(), photos_info), desc="Uploading photos", unit="file"):
        time.sleep(0.04)
        ya_disk.upload_file(url, info['file_name'])