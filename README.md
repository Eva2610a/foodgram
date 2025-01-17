**Продуктовый помощник (Foodrgam)** - дипломный проект.  
Проект представляет собой онлайн-сервис и API для него.

На этом сервисе пользователи смогут:

- публиковать свои рецепты
- подписываться на публикации других пользователей
- добавлять чужие рецепты в избранное
- создавать список продуктов, которые нужно купить для приготовления выбранных блюд

## Технологии:
![Python]
![Django]
![DjangoRestFramework]
![PostgreSQL]
![Docker]

## Особенности реализации
- Проект запускается в четырёх контейнерах — gateway, db, backend и frontend;
- Образы foodgram_frontend, foodgram_backend и foodgram_gateway запушены на DockerHub;
- Реализован workflow c автодеплоем на удаленный сервер и отправкой сообщения в Telegram;

## Развертывание на локальном сервере

- Создайте файл .env в корне проекта. Шаблон для заполнения файла находится в .env.example;
- Установите Docker и docker-compose (Про установку вы можете прочитать в [документации](https://docs.docker.com/engine/install/) и [здесь](https://docs.docker.com/compose/install/) про установку docker-compose.)
- Запустите docker compose, выполнив команду: `docker compose -f docker-compose.yml up --build -d`.
- Выполните миграции: `docker compose -f docker-compose.yml exec backend python manage.py migrate`.
- Создайте суперюзера: `docker compose -f docker-compose.yml exec backend python manage.py createsuperuser`.
- Соберите статику: `docker compose -f docker-compose.yml exec backend python manage.py collectstatic`.
- Заполните базу ингредиентами: `docker compose -f docker-compose.yml exec backend python manage.py load_ingredients`.
- Заполните базу ингредиентами: `docker compose exec backend bash -c "python manage.py load_tags"`.

## Авторы
    **Богунова Ева**


По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

Адрес сервера:

http://foodfoood234.zapto.org/recipes

