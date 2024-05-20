import os
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import requests

PROFILE_DIRR = f".\\temp\\profile"

# Функция для скачивания картинок
def download_images(url_list, output_dir):
    # Создание директории, если она не существует
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Загрузка каждой картинки из списка URL
    for index, url in enumerate(url_list, start=1):
        response = requests.get(url)
        if response.status_code == 200:
            # Определение расширения файла картинки
            image_extension = url.split('.')[-1].split('?')[0]
            image_filename = f"image_{index}.{image_extension}"
            image_path = os.path.join(output_dir, image_filename)

            # Сохранение картинки в файл
            with open(image_path, 'wb') as f:
                f.write(response.content)
                print(f"Downloaded {image_filename} to {output_dir}")
        else:
            print(f"Failed to download image from {url}")

# Настройка профиля виртуальной машины Chrome
options = uc.ChromeOptions()
# Установка директории профиля
options.user_data_dir = f'--user-data-dir={PROFILE_DIRR}'
options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
options.add_argument('--headless')  # Запуск в безголовом режиме
options.add_argument('--disable-gpu')  # Отключение GPU для совместимости

# Инициализация драйвера Chrome
driver = uc.Chrome(options=options, version_main=114)
actions = ActionChains(driver)

urlsite = 'https://testsite.test'
# Словарь для хранения URL-адресов карт
sitemap_dict = {
    'sitemap.txt': f'{urlsite}/post-sitemap.xml',
    'sitemap_category.txt': f'{urlsite}/category-sitemap.xml'
}

# Словарь для хранения данных о страницах
sitemap_data = {
    'страницы с группами': {},
    'страницы с новостями': {}
}

# Словарь для отслеживания прогресса
progress_dict = {}

# Обработка каждой карты сайта
for filename, sitemap_url in sitemap_dict.items():
    # Загрузка страницы карты сайта
    driver.get(sitemap_url)

    # Получение содержимого страницы
    main_page = driver.page_source
    soup = BeautifulSoup(main_page, 'html.parser')
    soup = soup.find('tbody')

    # Сохранение содержимого страницы в файл
    with open(filename, "w", encoding='utf-8') as write_file:
        write_file.write(str(soup))

    # Извлечение всех ссылок на статьи
    elements = soup.find_all('a')
    for idx, element in enumerate(elements, start=1):
        link = element.get('href')
        sitemap_data['страницы с новостями'][link] = {}

# Сохранение данных карты сайта в JSON файл
with open("sitemap_data.json", "w") as write_file:
    json.dump(sitemap_data, write_file)

# Инициализация словаря процесса
process_dict = {}

# Обработка текущего прогресса
current_progress = sitemap_data['страницы с новостями']
for url in process_dict:
    del current_progress[url]
current_progress_href_edition = current_progress

# Парсинг страниц с статьями
for url_page in current_progress:
    process_dict[url_page] = {'url': {}, 'href': {}}

    # Загрузка страницы
    driver.get(url_page)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    soup = soup.find('main')

    # Список тегов для извлечения данных
    tags_to_find = ['a', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'img', 'alt', 'href', 'src', 'data-lazy-src', 'div', 'span', 'strong', 'em', 'b', 'i', 'u', 'small', 'mark', 'code', 'pre', 'q']

    parsed_data = []

    # Извлечение данных из тегов
    elements = soup.find_all(tags_to_find)
    for idx, element in enumerate(elements, start=1):
        tag_name = element.name
        if tag_name == 'img':
            # Обработка картинок
            if element.get('data-lazy-src'):
                imgurl = element.get('data-lazy-src')
                file_name_oldsite = imgurl[50:]
                imgurl = 'сайт.ру/images/' + imgurl[50:]
                process_dict[url_page]['url'][file_name_oldsite] = {'url': imgurl + file_name_oldsite}

            if element.get('alt'):
                alt_str = element.get('alt')
                process_dict[url_page]['url'][file_name_oldsite]['alt'] = alt_str

            final_img_str = f"""
<img alt="{alt_str}" data-lazy-src="{imgurl}" />"""
            parsed_data.append(('img', final_img_str, idx))
        else:
            # Обработка остальных тегов
            item_content = element.text
            if element.get('href'):
                hr = str(element.get('href'))
                hr = 'сайт.ру/blog/' + hr[23:]
                final_href_link = f"""<a href='{hr}'>{element.text}</a>"""
                parsed_data.append(('a', final_href_link, idx))

                process_dict[url_page]['href'][hr] = {'url': hr, 'text': str(element.text)}
                current_progress_href_edition[hr] = {}

            parsed_data.append((tag_name, element.text, idx))

    # Генерация имени файла на основе URL
    new_url_page = 'сайт.ру/blog/' + url_page[23:]
    with open(f'./pages/{new_url_page}_nocode.txt', 'w', encoding='utf-8') as file:
        for tag_name, item_content, idx in parsed_data:
            file.write(f"Order: {idx}, {tag_name.capitalize()}: {item_content}\n")

    with open(f'./pages/{new_url_page}.txt', 'w', encoding='utf-8') as file:
        for tag_name, item_content, idx in parsed_data:
            file.write(f"{item_content}\n")

    progress_dict[url_page] = {}

# Сохранение прогресса в JSON файл
with open("progress_dict.json", "w") as write_file:
    json.dump(progress_dict, write_file)

