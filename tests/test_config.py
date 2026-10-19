
"""Тесты проверки конфигурации."""

import tempfile
import unittest
from pathlib import Path

from src.main import read_config, validate_config


# Корректная конфигурация, от которой будем отталкиваться в тестах.
VALID_CONFIG = {
    "package_name": "curl",
    "repository": "https://example.org/alpine/main",
    "test_mode": "false",
    "package_version": "8.10.1-r0",
    "output_image": "dependency_graph.png",
    "package_filter": "",
}


def write_xml(path: Path, config: dict[str, str]) -> None:
    """Создаёт XML для теста без необходимости хранить отдельные файлы."""

    fields = "\n".join(
        f"    <{key}>{value}</{key}>"
        for key, value in config.items()
    )

    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<config>\n{fields}\n</config>\n",
        encoding="utf-8",
    )


class ConfigTests(unittest.TestCase):

    def test_valid_config(self):
        """Корректные параметры не должны вызывать ошибки."""

        errors = validate_config(VALID_CONFIG)
        self.assertEqual(errors, [])

    def test_empty_package_name(self):
        """Пустое название пакета должно быть отклонено."""

        config = VALID_CONFIG.copy()
        config["package_name"] = ""

        errors = validate_config(config)
        self.assertTrue(any("package_name" in error for error in errors))

    def test_invalid_test_mode(self):
        """Режим должен принимать только true или false."""

        config = VALID_CONFIG.copy()
        config["test_mode"] = "yes"

        errors = validate_config(config)
        self.assertTrue(any("test_mode" in error for error in errors))

    def test_invalid_repository(self):
        """Некорректный URL должен быть отклонён."""

        config = VALID_CONFIG.copy()
        config["repository"] = "not-a-url"

        errors = validate_config(config)
        self.assertTrue(any("repository" in error for error in errors))

    def test_invalid_version(self):
        """Версия с неправильным форматом должна быть отклонена."""

        config = VALID_CONFIG.copy()
        config["package_version"] = "version-one"

        errors = validate_config(config)
        self.assertTrue(any("package_version" in error for error in errors))

    def test_invalid_image_name(self):
        """Имя изображения должно иметь расширение PNG."""

        config = VALID_CONFIG.copy()
        config["output_image"] = "graph.jpg"

        errors = validate_config(config)
        self.assertTrue(any("output_image" in error for error in errors))

    def test_xml_is_read(self):
        """Приложение должно правильно прочитать XML."""

        with tempfile.TemporaryDirectory() as directory:
            xml_path = Path(directory) / "config.xml"
            write_xml(xml_path, VALID_CONFIG)

            config = read_config(str(xml_path))

            self.assertEqual(config["package_name"], "curl")
            self.assertEqual(config["test_mode"], "false")

    def test_missing_xml(self):
        """Несуществующий файл должен вызвать понятную ошибку."""

        with tempfile.TemporaryDirectory() as directory:
            xml_path = Path(directory) / "missing.xml"

            with self.assertRaises(Exception):
                read_config(str(xml_path))


if __name__ == "__main__":
    unittest.main()
