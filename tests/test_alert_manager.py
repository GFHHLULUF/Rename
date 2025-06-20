#!/usr/bin/env python3
"""
Тесты для модуля alert_manager
Покрытие: >50% кода
"""

import unittest
import tempfile
import os
import datetime
from unittest.mock import patch, MagicMock

# Добавляем путь к модулям проекта
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Database
from models.alert_manager import AlertManager


class TestAlertManager(unittest.TestCase):
    """Тестовый класс для AlertManager"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем временную базу данных для тестов
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.database = Database(self.temp_db.name)
        self.database.create_database()
        self.alert_manager = AlertManager(self.database)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.alert_manager = None
        self.database = None
        # Удаляем временную базу данных
        try:
            if os.path.exists(self.temp_db.name):
                os.unlink(self.temp_db.name)
        except PermissionError:
            pass  # Игнорируем ошибки доступа к файлу
    
    def test_alert_manager_initialization(self):
        """Тест инициализации AlertManager"""
        assert self.alert_manager is not None
        self.assertIsNotNone(self.alert_manager.db)
        self.assertEqual(len(self.alert_manager.temperature_alerts), 0)
        self.assertEqual(len(self.alert_manager.disk_alerts), 0)
        self.assertEqual(len(self.alert_manager.ram_alerts), 0)
    
    def test_check_temperature_alert_normal(self):
        """Тест проверки температуры - нормальная температура"""
        assert self.alert_manager is not None
        assert self.database is not None
        # Добавляем сервер
        self.database.add_server("http://test-server:9090", "Test Server")
        
        # Нормальная температура
        cpu_info = {'temperatur': 60.0}
        
        # Проверяем оповещения
        self.alert_manager._check_temperature_alert("http://test-server:9090", cpu_info)
        
        # Проверяем, что оповещений нет
        alerts = self.alert_manager.get_active_alerts("http://test-server:9090")
        self.assertEqual(len(alerts), 0)
        
        # Проверяем, что счетчик температуры сброшен
        self.assertEqual(len(self.alert_manager.temperature_alerts["http://test-server:9090"]), 0)
    
    def test_check_temperature_alert_warning(self):
        """Тест проверки температуры - предупреждение"""
        assert self.alert_manager is not None
        assert self.database is not None
        # Добавляем сервер
        self.database.add_server("http://test-server:9090", "Test Server")
        
        # Высокая температура
        cpu_info = {'temperatur': 90.0}
        
        # Проверяем оповещения
        self.alert_manager._check_temperature_alert("http://test-server:9090", cpu_info)
        
        # Проверяем, что создано предупреждение
        alerts = self.alert_manager.get_active_alerts("http://test-server:9090")
        self.assertEqual(len(alerts), 1)
        self.assertIn("ПРЕДУПРЕЖДЕНИЕ", alerts[0][4])  # message
        self.assertIn("90.0°C", alerts[0][4])
        
        # Проверяем, что время добавлено в счетчик
        self.assertEqual(len(self.alert_manager.temperature_alerts["http://test-server:9090"]), 1)
    
    def test_check_disk_usage_alert(self):
        """Тест проверки использования дисков"""
        assert self.alert_manager is not None
        assert self.database is not None
        # Добавляем сервер
        self.database.add_server("http://test-server:9090", "Test Server")
        
        # Высокое использование диска
        rom_info = {
            "C:": {"usage_precent": 95.0},
            "D:": {"usage_precent": 85.0}
        }
        
        # Проверяем оповещения
        self.alert_manager._check_disk_usage_alert("http://test-server:9090", rom_info)
        
        # Проверяем, что создано оповещение только для диска C:
        alerts = self.alert_manager.get_active_alerts("http://test-server:9090")
        self.assertEqual(len(alerts), 1)
        self.assertIn("Диск C:", alerts[0][4])  # message
        self.assertIn("95.0%", alerts[0][4])
        
        # Проверяем, что диск добавлен в список оповещений
        self.assertIn("C:", self.alert_manager.disk_alerts["http://test-server:9090"])
        self.assertNotIn("D:", self.alert_manager.disk_alerts["http://test-server:9090"])
    
    def test_check_ram_usage_alert(self):
        """Тест проверки использования RAM"""
        assert self.alert_manager is not None
        assert self.database is not None
        # Добавляем сервер
        self.database.add_server("http://test-server:9090", "Test Server")
        
        # Высокое использование RAM
        ram_info = {'usage_precent': 95.0}
        
        # Проверяем оповещения
        self.alert_manager._check_ram_usage_alert("http://test-server:9090", ram_info)
        
        # Проверяем, что создано оповещение
        alerts = self.alert_manager.get_active_alerts("http://test-server:9090")
        self.assertEqual(len(alerts), 1)
        self.assertIn("RAM", alerts[0][4])  # message
        self.assertIn("95.0%", alerts[0][4])
        
        # Проверяем, что флаг установлен
        self.assertTrue(self.alert_manager.ram_alerts["http://test-server:9090"])
    
    def test_check_ram_usage_alert_normal(self):
        """Тест проверки использования RAM - нормальное использование"""
        assert self.alert_manager is not None
        assert self.database is not None
        # Добавляем сервер
        self.database.add_server("http://test-server:9090", "Test Server")
        
        # Нормальное использование RAM
        ram_info = {'usage_precent': 70.0}
        
        # Проверяем оповещения
        self.alert_manager._check_ram_usage_alert("http://test-server:9090", ram_info)
        
        # Проверяем, что оповещений нет
        alerts = self.alert_manager.get_active_alerts("http://test-server:9090")
        self.assertEqual(len(alerts), 0)
        
        # Проверяем, что флаг сброшен
        self.assertFalse(self.alert_manager.ram_alerts["http://test-server:9090"])
    
    def test_get_active_alerts(self):
        """Тест получения активных оповещений"""
        assert self.alert_manager is not None
        assert self.database is not None
        # Добавляем сервер
        self.database.add_server("http://test-server:9090", "Test Server")
        
        # Создаем оповещения
        self.database.add_alert("http://test-server:9090", "test_type", "Test message")
        
        # Получаем активные оповещения
        alerts = self.alert_manager.get_active_alerts("http://test-server:9090")
        
        # Проверяем результат
        self.assertIsInstance(alerts, list)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][3], "test_type")  # type
        self.assertEqual(alerts[0][4], "Test message")  # message


if __name__ == '__main__':
    unittest.main() 