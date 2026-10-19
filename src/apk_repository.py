
"Работа с индексом пакетов Alpine Linux."

import io
import tarfile
from urllib.error import URLError
from urllib.request import urlopen


class RepositoryError(Exception):
    "Ошибка получения или чтения индекса репозитория."

"Скачиваем APKINDEX.tar.gz и возвращаем содержимое APKINDEX."
def download_index(repository_url: str) -> str:


    # Убираем завершающий /, чтобы корректно собрать URL.
    index_url = repository_url.rstrip("/") + "/APKINDEX.tar.gz"

    try:
        # Используем стандартный urllib
        with urlopen(index_url, timeout=20) as response:
            archive_data = response.read()

    except (URLError, TimeoutError, OSError) as error:
        raise RepositoryError(
            f"Не удалось загрузить индекс репозитория: {error}"
        ) from error

    try:
        # Индекс находится внутри tar.gz-архива.
        with tarfile.open(
            fileobj=io.BytesIO(archive_data),
            mode="r:gz",
        ) as archive:
            index_file = archive.extractfile("APKINDEX")

            if index_file is None:
                raise RepositoryError("В архиве отсутствует файл APKINDEX")

            return index_file.read().decode("utf-8")

    except (tarfile.TarError, KeyError, UnicodeDecodeError) as error:
        raise RepositoryError(
            f"Не удалось прочитать индекс APKINDEX: {error}"
        ) from error


def parse_packages(index_text: str) -> list[dict[str, str]]:
    "Разбирает текст APKINDEX на отдельные записи пакетов."

    packages = []

    # Каждая запись пакета отделяется пустой строкой.
    for record in index_text.split("\n\n"):
        package = {}

        for line in record.splitlines():
            # Строки индекса имеют формат: буква поля и двоеточие.
            if len(line) >= 2 and line[1] == ":":
                field_name = line[0]
                field_value = line[2:].strip()
                package[field_name] = field_value

        # P — имя пакета, V — версия, D — зависимости.
        if "P" in package and "V" in package:
            packages.append(package)

    return packages


def get_direct_dependencies(
    repository_url: str,
    package_name: str,
    package_version: str,
) -> list[str]:
    "Возвращает прямые зависимости выбранного пакета."

    index_text = download_index(repository_url)
    packages = parse_packages(index_text)

    # Ищем пакет по имени и версии, а не только по имени.
    for package in packages:
        if (
            package.get("P") == package_name
            and package.get("V") == package_version
        ):
            dependencies = package.get("D", "")

            # В APKINDEX зависимости перечислены через пробелы.
            return dependencies.split() if dependencies else []

    raise RepositoryError(
        f"Пакет {package_name} версии {package_version} "
        "не найден в репозитории"
    )
