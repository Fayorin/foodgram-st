# О проекте: Foodgram

**Foodgram** — это веб-приложение, предоставляющее пользователям возможность делиться своими рецептами, сохранять понравившиеся блюда в избранное и подписываться на других авторов. Дополнительно авторизованные пользователи могут формировать список необходимых ингредиентов для готовки с помощью функции «Список покупок».

## Как запустить проект
Для корректной работы проекта необходимы Docker и Docker Compose.


### Настройка окружения

1. Клонируйте репозиторий проекта:
    ```bash
    git clone https://github.com/Fayorin/foodgram-st.git
    cd foodgram-st
    ```

2. Cоздайте файл `.env` в корневом каталоге и укажите в нём переменные:
    ```env
    POSTGRES_USER=django_user
    POSTGRES_PASSWORD=django_password
    POSTGRES_DB=django

    DB_HOST=db
    DB_PORT=5432

    ALLOWED_HOSTS="127.0.0.1 localhost"
    ```

### Сборка и запуск контейнеров

1. Запустите сборку и запуск контейнеров:

    ```bash
    docker compose up --build
    ```
    
2. Проведите миграции базы данных:

    ```bash
    docker compose exec backend python manage.py migrate --noinput
    ```
    
3. Скопируйте статические файлы:

    ```bash
    docker compose exec backend python manage.py collectstatic --no-input
    ```
    
4. Загрузите данные об ингредиентах:

    ```bash
    docker compose exec backend python manage.py import_ingredients
    ```
    
5. Импортируйте тестовых пользователей:

    ```bash
    docker compose exec backend python manage.py loaddata test_data.json
    ```
    
5. Создайте супер пользователя:
    ```bash
    docker compose exec backend python manage.py createsuperuser
    ```

6. После запуска контейнеров проект будет доступен по следующим адресам:

    - Главная страница: [http://127.0.0.1:8000](http://127.0.0.1:8000)
    - Админ-панель Django: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
    - Документация API: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)


### Установка Docker

Если Docker не установлен на вашем устройстве, следуйте инструкциям для соответствующей платформы:

- **[Docker для Windows](https://docs.docker.com/docker-for-windows/install/)**
- **[Docker для macOS](https://docs.docker.com/docker-for-mac/install/)**
- **[Docker для Linux](https://docs.docker.com/engine/install/)**