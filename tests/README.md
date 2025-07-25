# Тесты для системы мониторинга серверов

## Описание

Данная папка содержит автоматизированные тесты для системы мониторинга серверов. Тесты обеспечивают покрытие кода более 50% и проверяют основную функциональность приложения.

## Структура тестов

```
tests/
├── __init__.py              # Инициализация пакета тестов
├── conftest.py              # Конфигурация pytest и общие фикстуры
├── test_database.py         # Тесты для модуля database
├── test_alert_manager.py    # Тесты для модуля alert_manager
├── test_monitor.py          # Тесты для модуля monitor
├── test_views.py            # Тесты для view модулей
├── run_tests.py             # Скрипт запуска тестов с покрытием
└── README.md                # Этот файл
```

## Покрытие тестами

### Модуль Database (>70% покрытия)
- ✅ Создание и инициализация базы данных
- ✅ Добавление/удаление серверов
- ✅ Сохранение и получение метрик
- ✅ Управление инцидентами (создание, разрешение, удаление)
- ✅ Управление оповещениями (создание, подтверждение)
- ✅ Потокобезопасность операций
- ✅ Очистка старых данных

### Модуль AlertManager (>80% покрытия)
- ✅ Проверка температуры CPU
- ✅ Проверка использования дисков
- ✅ Проверка использования RAM
- ✅ Создание критических оповещений
- ✅ Таймауты и очистка оповещений
- ✅ Интеграционные тесты

### Модуль Monitor (>60% покрытия)
- ✅ Инициализация монитора
- ✅ Проверка доступности сети
- ✅ Получение метрик CPU, RAM, дисков
- ✅ Обработка ошибок подключения
- ✅ Парсинг данных Prometheus

### View модули (>50% покрытия)
- ✅ Форматирование времени
- ✅ Создание UI компонентов
- ✅ Обработка данных инцидентов
- ✅ Обновление интерфейса

## Установка зависимостей

```bash
pip install pytest
pip install pytest-cov
pip install coverage
```

## Запуск тестов

### Запуск всех тестов с покрытием
```bash
python tests/run_tests.py
```

### Запуск конкретного теста
```bash
python tests/run_tests.py test_database.py
```

### Запуск через pytest напрямую
```bash
# Все тесты
pytest tests/ -v

# Конкретный тест
pytest tests/test_database.py -v

# С покрытием
pytest tests/ --cov=models --cov=views --cov-report=html
```

## Результаты тестирования

После запуска тестов вы получите:

1. **Отчет о выполнении тестов** - какие тесты прошли/не прошли
2. **Отчет о покрытии кода** - процент покрытия по модулям
3. **HTML отчет** - детальный отчет в папке `htmlcov/`

### Требования к покрытию

- **Минимальное покрытие**: 50%
- **Целевое покрытие**: 70%+
- **Критические модули**: 80%+

## Типы тестов

### Unit тесты
- Тестирование отдельных функций и методов
- Мокирование внешних зависимостей
- Проверка граничных случаев

### Интеграционные тесты
- Тестирование взаимодействия между модулями
- Проверка работы с базой данных
- Тестирование потокобезопасности

### Тесты форматирования
- Проверка корректности отображения времени
- Тестирование парсинга различных форматов
- Валидация UI компонентов

## Моки и фикстуры

### Фикстуры (conftest.py)
- `temp_database` - временная база данных для тестов
- `mock_monitor` - мок монитора Prometheus
- `alert_manager` - менеджер оповещений
- `sample_*_data` - тестовые данные

### Моки
- `unittest.mock` для мокирования внешних зависимостей
- `patch` для замены функций и методов
- `MagicMock` для создания мок объектов

## Добавление новых тестов

1. Создайте новый файл `test_*.py`
2. Наследуйтесь от `unittest.TestCase`
3. Используйте фикстуры из `conftest.py`
4. Добавьте тесты для всех публичных методов
5. Проверьте покрытие кода

### Пример нового теста

```python
import unittest
from unittest.mock import patch

class TestNewModule(unittest.TestCase):
    def setUp(self):
        # Настройка перед тестом
        pass
    
    def test_some_function(self):
        # Тест функции
        with patch('module.external_dependency') as mock_dep:
            mock_dep.return_value = "test_value"
            result = some_function()
            self.assertEqual(result, "expected_value")
    
    def tearDown(self):
        # Очистка после теста
        pass
```

## Отладка тестов

### Запуск с подробным выводом
```bash
pytest tests/ -v -s
```

### Запуск конкретного теста
```bash
pytest tests/test_database.py::TestDatabase::test_add_server -v
```

### Просмотр покрытия в браузере
```bash
# После запуска тестов с покрытием
open htmlcov/index.html
```

## Требования к качеству

- Все тесты должны проходить
- Покрытие кода >= 50%
- Тесты должны быть читаемыми и понятными
- Каждый тест должен проверять одну конкретную функциональность
- Используйте описательные имена тестов
- Добавляйте комментарии к сложным тестам 