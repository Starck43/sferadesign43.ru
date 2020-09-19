#!/bin/bash
# parameter $1 - app name
# -r Обрабатывать папки и файлы рекурсивно.
if [ -n "$1" ] && [ "$1" == "help" ]
then
echo "Usage: bash startproject.sh [app-name]"
else
echo "Installing Virtual Environment..."
python3 -m venv ./venv


echo "Installing Django & requirements..."
if [ -f "./requirements.txt" ]
then
pip3 install -r requirements.txt
else
pip3 install django #djangorestframework
pip3 freeze
fi

if read -t 10 -p "Enter project name (default: 'crm'): " name
then
django-admin startproject $name .
else
django-admin startproject crm .
fi

touch $name/admin.py $name/models.py

if [ -n "$1" ]
then
name=$1
else
echo -n "Enter your app name: "
read name
fi

django-admin startapp $name
mkdir ./$name/templatetags
touch ./$name/templatetags/__init__.py

fi