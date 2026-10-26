
"Построение графа и поиск обратных зависимостей."

from collections import deque


def build_graph(
    repository_graph: dict[str, list[str]],
    start_package: str,
    package_filter: str = "",
) -> dict[str, list[str]]:
    "Обходит зависимости от начального пакета и строит подграф."

    if start_package not in repository_graph:
        raise ValueError(f"Пакет {start_package!r} не найден в репозитории")

    # Если имя содержит фильтр, пакет исключается из анализа.
    if package_filter and package_filter in start_package:
        return {}

    graph = {}
    visited = set()
    queue = deque([start_package])

    # Обычный BFS выполняется очередью.
    # Рекурсивная функция добавляет найденные вершины и их связи.
    def visit_next():
        if not queue:
            return

        package = queue.popleft()

        if package in visited:
            visit_next()
            return

        visited.add(package)
        graph.setdefault(package, [])

        for dependency in repository_graph.get(package, []):
            # Не включаем пакеты, чьё имя содержит фильтр.
            if package_filter and package_filter in dependency:
                continue

            graph[package].append(dependency)

            if dependency not in visited:
                queue.append(dependency)

        visit_next()

    visit_next()
    return graph


def find_reverse_dependencies(
    graph: dict[str, list[str]],
    target_package: str,
) -> list[str]:
    "Возвращает все пакеты в графе, которые зависят от целевого."

    if target_package not in graph:
        return []

    # Строим обратные связи: зависимость -> список использующих её пакетов.
    reverse_graph = {}

    for package, dependencies in graph.items():
        for dependency in dependencies:
            reverse_graph.setdefault(dependency, []).append(package)

    result = []
    visited = {target_package}
    queue = deque([target_package])

    # Обходим обратный граф, чтобы найти также транзитивные зависимости.
    while queue:
        current = queue.popleft()

        for dependent in reverse_graph.get(current, []):
            if dependent not in visited:
                visited.add(dependent)
                result.append(dependent)
                queue.append(dependent)

    return sorted(result)
