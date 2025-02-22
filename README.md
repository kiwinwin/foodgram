Доменное имя: https://kiwifoodgram.duckdns.org/
IP-адрес: 89.169.167.246:8080

# Проект "Foodgram"
# Описание проекта

Проект "Foodgram" выполнен в рамках финального задания спринта №18 образовательного курса "Python-разработчик" в целях применения и демонтрации навыков, полученных на протяжении всего курса.
Проект "Foodgram" - это ресурс, который предоставляет возможности публикации и просмотра рецептов, добавление их в избранное и список покупок, подписки на публикации авторов рецептов.


## Разграничение прав доступа

Анонимному пользователю доступны следующие действия:
1. регистрация и авторизация;
2. просмотр главной страницы со списком отсортированнных рецептов и их фильтрация;
3. просмотр профилей зарегистрированных пользоватлей с их рецептами;
4. просмотр отдельной публикации рецепта;
5. получение короткой ссылки на рецепт.

Зарегистрированному пользователю доступны те же действия, что и незарегистрированному, в также:
1.создание публикации своих рецептов с указанием следующих характеристик:
- название,
- описание,
- теги, 
- время приготовления,
- ингредиенты и их количество;
- картинка рецепта.
2. редактирование и удаление собственных рецептов;
3. добавление в избранное рецептов других пользователей;
4. добавление в список покупок рецептов (ингредиентов) - количество повторяющихся в рецептах ингредиентов суммируется;
5. возможность подписываться на публикации других пользователей.
6. смена аватара профиля;
7. смена пароля; 
8. выход из системы.

Администртору системы доступны все права зарегистрированного ползователя, а также:
1. Создание, удаление и блокировка аккаунтов ползователей;
2. изменение пароля любого ползователя;
3. создание, редактирование и удаление тегов и ингредиентов;
4. редактирование и удаление любых рецептов.


## Стек технологий

Django 4.2.16
djangorestframework 3.15.2
djoser 2.2.3
gunicorn 20.1.0
Pillow 10.4.0
psycopg2-binary 2.9.10


## Инструкция по запуску

1. форкнуть репозиторий проекта: kiwinwin/foodgram
2. клонировать форкнутый репозиторий
3. в репозитории проекта во вкладке settings/Secrets and variables/actions определить ваши secrets: Логин и пароль вашего профиля на Docker.com:
* DOCKER_PASSWORD
* DOCKER_USERNAME
* Данные вашего удалённого сервера:
  - HOST (IP-адрес вашего сервера)
  - SSH_KEY (закрытый SSH-ключ)
  - USER (имя пользователя)
  - SSH_PASSPHRASE (passphrase от закрытого SSH-ключа) 
4. на сервере:
* создайте директорию foodgram и создайте в ней файл .env. В файле .env определите значения переменных SECRET_KEY и ALLOWED_HOSTS;
* определите настройки location в секции server в файле /etc/nginx/sites-enabled/default: server { server_name <IP-адрес вашего сервера> <доменное имя вашего сайта>; location / { proxy_set_header Host $http_host; proxy_pass http://127.0.0.1:8080; } }
* в директории проекта в файле docker-compose.production.yml замените строчки с указанием image: kiwinwin/... на ваш image: <логин вашего профиля на Docker.com>
5. сделайте пуш: git add . git commit -m "<ваше сообщение коммита>" git push
6. дождитесь результатов actions main.yml и, если deploy прошёл успешно и в вашей БД нет тегов и ингредиентов, запустите actions import_tags_ingredients.yml.


## Эндпоинты

https://kiwifoodgram.duckdns.org/signup - регистрация нового пользователя;
https://kiwifoodgram.duckdns.org/signin - войти на сайт;
https://kiwifoodgram.duckdns.org/about - о проекте;
https://kiwifoodgram.duckdns.org/technologies - технологии;
https://kiwifoodgram.duckdns.org/recipes - главная страница сайта со списком всех рецептов;
https://kiwifoodgram.duckdns.org/recipes/create - создание нового рецепта;
https://kiwifoodgram.duckdns.org/cart - просмотр рецептов, добавленных в список покупок;
https://kiwifoodgram.duckdns.org/favorites - просмотр списка избранных рецептов;
https://kiwifoodgram.duckdns.org/subscriptions - просмотр списка подписок на других пользователей;
https://kiwifoodgram.duckdns.org/logout - выход из системы.


## Примеры запросов к API проекта

Регистрация нового пользователя

POST http://kiwifoodgram.duckdns.org/api/recipes/

{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов",
  "password": "Qwerty123"
}

Получение списка рецептов
GET http://kiwifoodgram.duckdns.org/api/recipes/
{
  "count": 123,
  "next": "http://kiwifoodgram.duckdns.org/api/recipes/?page=4",
  "previous": "http://kiwifoodgram.duckdns.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Иванов",
        "is_subscribed": false,
        "avatar": "http://kiwifoodgram.duckdns.org/media/users/image.png"
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://kiwifoodgram.duckdns.org/media/recipes/images/image.png",
      "text": "string",
      "cooking_time": 1
    }
  ]
}

## Авторы

команда Яндекс Практикума [yandex-praktikum] (https://github.com/yandex-praktikum)
Галия Байбулова [kiwinwin] (https://github.com/kiwinwin)
