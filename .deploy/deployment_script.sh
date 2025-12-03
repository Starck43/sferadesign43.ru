#!/bin/bash

set -e # Exit on error

PROJECT_NAME=$1
PROJECT_DIR=$2
DJANGO_ADMIN_EMAIL=$3
DJANGO_ADMIN_SUPERUSER=$4
DJANGO_ADMIN_PASSWORD=$5
VENV_DIR=$PROJECT_DIR/venv
PIP=$VENV_DIR/bin/pip
PYTHON=$VENV_DIR/bin/python

if [ ! -f "$PROJECT_DIR"/.env ]; then
    echo "File .env does not exist! Process aborted."
    echo "Please create it before running the script."
    exit 1
fi

# Проверяем существование виртуального окружения
if [ ! -d "$VENV_DIR" ]; then
    python3.12 -m venv "$VENV_DIR"
    $PIP install -r "$PROJECT_DIR"/requirements.txt
    $PIP install --upgrade pip

    mkdir -p "$PROJECT_DIR"/media
    mkdir -p "$PROJECT_DIR"/static
    chown -R starck:starck "$PROJECT_DIR"

    $PYTHON "$PROJECT_DIR"/manage.py migrate auth --noinput
    $PYTHON "$PROJECT_DIR"/manage.py migrate --noinput
    $PYTHON "$PROJECT_DIR"/manage.py collectstatic --noinput

    echo "Creating superuser"
    printf "from django.contrib.auth.models import User\nUser.objects.create_superuser('%s', '%s', '%s')" \
        "$DJANGO_ADMIN_SUPERUSER" "$DJANGO_ADMIN_EMAIL" "$DJANGO_ADMIN_PASSWORD" | \
        $PYTHON "$PROJECT_DIR"/manage.py shell

    echo "Created a new Python environment."

    # ПЕРВЫЙ ЗАПУСК: устанавливаем конфиги systemd и nginx
    echo "Setting up systemd services..."
    sudo cp "$PROJECT_DIR/.deploy/gunicorn.service" /etc/systemd/system/sd43.service
    sudo cp "$PROJECT_DIR/.deploy/gunicorn.socket" /etc/systemd/system/sd43.socket

    echo "Setting up nginx..."
    sudo cp "$PROJECT_DIR/.deploy/nginx.conf" /etc/nginx/sites-available/sd43
    sudo ln -sf /etc/nginx/sites-available/sd43 /etc/nginx/sites-enabled/

    # Включаем автозагрузку
    sudo systemctl enable sd43.socket
    sudo systemctl enable sd43.service

    sudo nginx -t

    # Запускаем daemon-reload (после установки)
    sudo systemctl daemon-reload
    sudo systemctl restart nginx

else
    $PIP install pip --upgrade
    $PIP install -r "$PROJECT_DIR"/requirements.txt --upgrade
    echo "Packages updated."
fi

$PYTHON "$PROJECT_DIR"/manage.py makemigrations --noinput
$PYTHON "$PROJECT_DIR"/manage.py migrate --noinput

# ТОЛЬКО если файлы были изменены (проверяем дату)
CONFIG_CHANGED=false
if [ -f "$PROJECT_DIR/.deploy/gunicorn.service" -a -f /etc/systemd/system/sd43.service ]; then
    if [ "$PROJECT_DIR/.deploy/gunicorn.service" -nt /etc/systemd/system/sd43.service ]; then
        echo "Updating systemd service (config changed)..."
        sudo cp "$PROJECT_DIR/.deploy/gunicorn.service" /etc/systemd/system/sd43.service
        CONFIG_CHANGED=true
    fi
fi

if [ -f "$PROJECT_DIR/.deploy/gunicorn.socket" -a -f /etc/systemd/system/sd43.socket ]; then
    if [ "$PROJECT_DIR/.deploy/gunicorn.socket" -nt /etc/systemd/system/sd43.socket ]; then
        echo "Updating systemd socket (config changed)..."
        sudo cp "$PROJECT_DIR/.deploy/gunicorn.socket" /etc/systemd/system/sd43.socket
        CONFIG_CHANGED=true
    fi
fi

if [ -f "$PROJECT_DIR/.deploy/nginx.conf" -a -f /etc/nginx/sites-available/sd43 ]; then
    if [ "$PROJECT_DIR/.deploy/nginx.conf" -nt /etc/nginx/sites-available/sd43 ]; then
        echo "Updating nginx config (config changed)..."
        sudo cp "$PROJECT_DIR/.deploy/nginx.conf" /etc/nginx/sites-available/sd43
        CONFIG_CHANGED=true
    fi
fi

# Если конфиги менялись - перезагружаем systemd и nginx
if [ "$CONFIG_CHANGED" = true ]; then
    echo "Configuration changed, reloading services..."
    sudo systemctl daemon-reload

    if sudo nginx -t; then
        sudo systemctl reload nginx
    else
        echo "ERROR: Nginx configuration test failed!"
        exit 1
    fi
fi

# Перезапускаем приложение (после миграций и обновления пакетов)
echo "Restarting application..."
sudo systemctl restart sd43.service

# Проверяем статус
echo "Checking service status..."
sleep 2
if ! sudo systemctl is-active sd43.service >/dev/null 2>&1; then
    echo "ERROR: Service is not running!"
    sudo systemctl status sd43.service --no-pager
    exit 1
fi

echo "✅ Deployment completed for $PROJECT_NAME"

