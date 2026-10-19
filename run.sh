#!/bin/bash

# Выходим из скрипта при любой ошибке
set -e

# Проверяем, существует ли виртуальное окружение, и активируем его
if [ -d ".venv/bin" ]; then
    source .venv/bin/activate
elif [ -d "venv/bin" ]; then
    source venv/bin/activate
fi

# Запускаем программу, передавая ей все аргументы командной строки (если они есть)
python3 src/main.py "$@"