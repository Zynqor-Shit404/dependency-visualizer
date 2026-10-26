
"Получение зависимостей из Alpine Linux и тестового репозитория."

import io
import tarfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


class RepositoryError(Exception):
    "Ошибка получения или разбора репозитория."


def download_index(repository_url: str) -> str:
    "Скачивает APKINDEX.tar.gz и возвращает текст APKINDEX."

    url = repository_url.rstrip("/") + "/APKINDEX.tar.gz"

    try:
        with urlopen(url, timeout=20) as response:
            archive_data = response.read()
    except (URLError, TimeoutError, OSError) as error:
        raise RepositoryError(f"Не удалось загрузить индекс: {error}") from error

    try:
        with tarfile.open(fileobj=io.BytesIO(archive_data), mode="r:gz") as archive:
            index_file = archive.extractfile("APKINDEX")
            if index_file is None:
                raise RepositoryError("В архиве отсутствует APKINDEX")
            return index_file.read().decode("utf-8")
    except (tarfile.TarError, KeyError, UnicodeDecodeError) as error:
        raise RepositoryError(f"Не удалось прочитать APKINDEX: {error}") from error


def parse_packages(index_text: str) -> list[dict[str, str]]:
    "Преобразует записи APKINDEX в словари."

    packages = []

    for record in index_text.split("\n\n"):
        package = {}

        for line in record.splitlines():
            if len(line) >= 2 and line[1] == ":":
                package[line[0]] = line[2:].strip()

        if "P" in package and "V" in package:
            packages.append(package)

    return packages


def load_test_repository(file_path: str) -> dict[str, list[str]]:
    "Читает тестовый граф из строк вида A: B C."

    path = Path(file_path)

    if not path.is_file():
        raise RepositoryError(f"Тестовый файл не найден: {path}")

    graph = {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise RepositoryError(f"Не удалось прочитать тестовый файл: {error}") from error

    for line_number, line in enumerate(lines, start=1):
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            raise RepositoryError(
                f"Строка {line_number}: ожидается формат A: B C"
            )

        name, dependencies_text = line.split(":", maxsplit=1)
        name = name.strip()

        # В тестовом режиме имена пакетов должны быть большими латинскими буквами.
        if not name or not name.isascii() or not name.isalpha() or not name.isupper():
            raise RepositoryError(
                f"Строка {line_number}: имя пакета должно быть заглавными "
                "латинскими буквами"
            )

        dependencies = dependencies_text.split()

        for dependency in dependencies:
            if (
                not dependency.isascii()
                or not dependency.isalpha()
                or not dependency.isupper()
            ):
                raise RepositoryError(
                    f"Строка {line_number}: некорректное имя зависимости "
                    f"{dependency!r}"
                )

        graph[name] = dependencies

    # Добавляем вершины, которые встречаются только как зависимости.
    for dependencies in list(graph.values()):
        for dependency in dependencies:
            graph.setdefault(dependency, [])

    return graph


def load_alpine_repository(repository_url: str) -> dict[str, list[str]]:
    "Строит граф из индекса Alpine Linux."

    packages = parse_packages(download_index(repository_url))
    graph = {}

    for package in packages:
        name = package["P"]
        dependencies = package.get("D", "").split()
        graph[name] = dependencies

    return graph


def get_direct_dependencies(
    repository_url: str,
    package_name: str,
    package_version: str,
) -> list[str]:
    "Находит прямые зависимости заданной версии пакета Alpine."

    packages = parse_packages(download_index(repository_url))

    for package in packages:
        if package.get("P") == package_name and package.get("V") == package_version:
            return package.get("D", "").split()

    raise RepositoryError(
        f"Пакет {package_name} версии {package_version} не найден в репозитории"
    )
