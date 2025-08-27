#!/bin/bash

# Выходим при первой ошибке
set -e

# Проверяем, существует ли файл сервисного аккаунта в монтированном томе
echo "Checking FCM service account file..."
if [ -f /tmp/fcm_service_account.json ]; then
    echo "Found FCM file in mounted location. Copying to volume..."
    mkdir -p /app/firebase
    cp /tmp/fcm_service_account.json /app/firebase/fcm_service_account.json
    chmod 644 /app/firebase/fcm_service_account.json
    echo "FCM file successfully copied to volume."
elif [ -f /app/firebase/fcm_service_account.json ]; then
    echo "FCM service account file already exists in volume."
else
    echo "WARNING: FCM service account file not found! Push notifications will not work."
    echo "Please ensure fcm_service_account.json is mounted to /tmp/fcm_service_account.json"
fi

# Определяем путь к статике (должен совпадать с STATIC_ROOT в settings.py)
STATIC_DIR=/app/collected_static
FRONT_STATIC_DIR=/app/static

# Собираем статику Django
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Проверяем, существует ли volume для статики
VOLUME_STATIC_DIR=/app/backend_static  # Должен совпадать с путем в volumes в docker-compose
if [ -d "$VOLUME_STATIC_DIR" ]; then
    echo "Copying static files to volume directory..."
    # Удаляем старое содержимое и копируем новое
    rm -rf $VOLUME_STATIC_DIR/*
    cp -r $STATIC_DIR/* $VOLUME_STATIC_DIR/
    cp -r $FRONT_STATIC_DIR/* $VOLUME_STATIC_DIR/
else
    echo "Warning: Volume directory $VOLUME_STATIC_DIR not found!"
fi

# Создаем миграции
echo "Creating migrations..."
python manage.py makemigrations --noinput

# Выполняем миграции
echo "Applying database migrations..."
python manage.py migrate --noinput

# Запускаем основной процесс (команду из CMD)
exec "$@"