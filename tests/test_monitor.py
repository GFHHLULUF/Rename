#!/usr/bin/env python3
"""
Тесты для модуля monitor
Покрытие: >50% кода
"""

import unittest
from unittest.mock import patch, MagicMock
import os

# Добавляем путь к модулям проекта
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.monitor import PrometheusMonitor


class TestPrometheusMonitor(unittest.TestCase):
    """Тестовый класс для PrometheusMonitor"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.test_url = "http://test-server:9090"
        self.monitor = PrometheusMonitor(self.test_url)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.monitor = None
    
    def test_monitor_initialization(self):
        """Тест инициализации монитора"""
        self.assertIsNotNone(self.monitor)
        self.assertIsNotNone(self.monitor.prom)  # type: ignore[attr-defined]
        self.assertEqual(self.monitor.prom.url, self.test_url)  # type: ignore[attr-defined]
    
    def test_change_url(self):
        """Тест смены URL"""
        new_url = "http://new-server:9090"
        self.monitor.change_url(new_url)  # type: ignore
        self.assertEqual(self.monitor.prom.url, new_url)  # type: ignore[attr-defined]
    
    def test_parse_metric_value(self):
        """Тест парсинга значения метрики"""
        # Тестируем числовое значение
        result = self.monitor._parse_metric_value("45.2")  # type: ignore[attr-defined]
        self.assertEqual(result, 45.2)
        
        # Тестируем целое значение
        result = self.monitor._parse_metric_value("100")  # type: ignore[attr-defined]
        self.assertEqual(result, 100.0)
        
        # Тестируем некорректное значение
        result = self.monitor._parse_metric_value("invalid")  # type: ignore[attr-defined]
        self.assertEqual(result, 0.0)


if __name__ == '__main__':
    unittest.main() 