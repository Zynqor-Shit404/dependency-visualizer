
"CLI-приложение для этапа 1 варианта 11."

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET



# Все параметры, которые должны быть в XML.
REQUIRED_FIELDS = (
    "package_name",
    "repository",
    "test_mode",
    "package_version",
    "output_image",
    "package_filter",
)


class ConfigError(Exception):
    "Ошибка чтения или проверки конфигурации."



def read_config(config_path: str) -> dict[str, str]:
    "Читает XML и возвращает настройки в виде словаря."

    path = Path(config_path)

    # Проверяем, существует ли файл.
    if not path.is_file():
        raise ConfigError(f"Файл конфигурации не найден: {path}")

    # Читаем XML и обрабатываем ошибки его структуры.
    try:
        tree = ET.parse(path)
    except ET.ParseError as error:
        raise ConfigError(f"Некорректный XML: {error}") from error
    except OSError as error:
        raise ConfigError(f"Не удалось прочитать файл: {error}") from error

    root = tree.getroot()

    # Проверяем корневой XML-элемент.
    if root.tag != "config":
        raise ConfigError(
            "Корневой XML-элемент должен называться <config>"
        )

    config = {}

    # Считываем все параметры конфигурации.
    for field in REQUIRED_FIELDS:
        element = root.find(field)

        if element is None or element.text is None:
            config[field] = ""
        else:
            config[field] = element.text.strip()

    return config


def validate_config(config: dict[str, str]) -> list[str]:
    "Проверяет настройки и возвращает список ошибок."

    errors = []

    # Название пакета не должно быть пустым.
    if not config["package_name"]:
        errors.append("package_name: название пакета не может быть пустым")

    # Проверяем режим тестового репозитория.
    test_mode = config["test_mode"].lower()

    if test_mode not in ("true", "false"):
        errors.append("test_mode: допустимы только true или false")

    # Проверяем URL или путь к тестовому файлу.
    repository = config["repository"]

    if not repository:
        errors.append("repository: URL или путь не может быть пустым")
    elif test_mode == "true":
        if not Path(repository).is_file():
            errors.append(
                "repository: в тестовом режиме должен существовать "
                "локальный файл репозитория"
            )
    else:
        parsed_url = urlparse(repository)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            errors.append(
                "repository: ожидается корректный URL с http или https"
            )

    # Проверяем формат версии пакета.
    version = config["package_version"]
    version_pattern = r"^\d+\.\d+\.\d+(?:-r\d+)?$"

    if not re.fullmatch(version_pattern, version):
        errors.append(
            "package_version: ожидается формат, например 1.2.3 или 1.2.3-r0"
        )

    # Имя изображения должно быть файлом PNG без пути к каталогу.
    image_name = config["output_image"]

    if (
        not image_name
        or Path(image_name).name != image_name
        or Path(image_name).suffix.lower() != ".png"
    ):
        errors.append(
            "output_image: укажите имя файла без каталога, "
            "с расширением .png"
        )

    # Пустой фильтр допустим.
    if "package_filter" not in config:
        errors.append("package_filter: параметр отсутствует")

    return errors


def print_config(config: dict[str, str]) -> None:
    "Выводит настройки в формате ключ=значение."

    print("Параметры конфигурации:")

    for field in REQUIRED_FIELDS:
        print(f"{field} = {config[field]}")


def main() -> int:
    "Основная функция запуска приложения."

    # Позволяем передать путь к XML через аргумент командной строки.
    parser = argparse.ArgumentParser(
        description="Проверка конфигурации визуализатора зависимостей"
    )
    parser.add_argument(
        "--config",
        default="config.xml",
        help="Путь к XML-файлу конфигурации",
    )
    args = parser.parse_args()

    # Обрабатываем ошибки чтения и проверки конфигурации.
    try:
        config = read_config(args.config)
        errors = validate_config(config)

        # Если есть ошибки, выводим их и завершаем запуск.
        if errors:
            print("Ошибки конфигурации:", file=sys.stderr)

            for error in errors:
                print(f"- {error}", file=sys.stderr)

            return 1

        # На этапе 1 требуется вывести все настройки.
        print_config(config)
        return 0

    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


# Запускаем main только при непосредственном запуске файла/модуля.
if __name__ == "__main__":
    sys.exit(main())
