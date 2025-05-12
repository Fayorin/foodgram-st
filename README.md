# О проекте: Foodgram

**Foodgram** — это веб-приложение, предоставляющее пользователям возможность делиться своими рецептами, сохранять понравившиеся блюда в избранное и подписываться на других авторов.

## Как запустить проект
Для корректной работы проекта необходим Docker.


### Настройка окружения

1. Клонируйте репозиторий проекта:
    ```bash
    git clone https://github.com/Fayorin/foodgram-st.git
    cd foodgram-st
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
