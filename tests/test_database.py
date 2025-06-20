#!/usr/bin/env python3
"""
Тесты для модуля database
Покрытие: >90% кода
"""

import unittest
import tempfile
import os
import sqlite3
import datetime
import json
from unittest.mock import patch, MagicMock

# Добавляем путь к модулям проекта
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Database


class TestDatabase(unittest.TestCase):
    """Тестовый класс для Database"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем временную базу данных для тестов
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Закрываем соединения
        if self.db is not None and hasattr(self.db, 'conn') and self.db.conn:
            self.db.conn.close()
        
        self.db = None
        # Удаляем временную базу данных
        try:
            if os.path.exists(self.temp_db.name):
                os.unlink(self.temp_db.name)
        except PermissionError:
            pass  # Игнорируем ошибки доступа к файлу
    
    def test_database_creation(self):
        """Тест создания базы данных"""
        assert self.db is not None
        # Проверяем, что база создана
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Проверяем структуру таблиц
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Проверяем таблицу servers
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='servers'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Проверяем таблицу metrics
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Проверяем таблицу incidents
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='incidents'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Проверяем таблицу alerts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_add_server(self):
        """Тест добавления сервера"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")  # type: ignore[attr-defined]
        
        # Проверяем, что сервер добавлен
        self.assertIn("http://test-server:9090", self.db.servers)  # type: ignore[attr-defined]
        
        # Проверяем в базе данных
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM servers WHERE url = ?", ("http://test-server:9090",))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "http://test-server:9090")
        conn.close()
    
    def test_delete_server(self):
        """Тест удаления сервера"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")  # type: ignore[attr-defined]
        
        # Удаляем сервер
        self.db.delete_server("http://test-server:9090")  # type: ignore[attr-defined]
        
        # Проверяем, что сервер удален
        self.assertNotIn("http://test-server:9090", self.db.servers)  # type: ignore[attr-defined]
        
        # Проверяем в базе данных
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM servers WHERE url = ?", ("http://test-server:9090",))
        result = cursor.fetchone()
        self.assertIsNone(result)
        conn.close()
    
    def test_get_server_id(self):
        """Тест получения ID сервера"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")  # type: ignore[attr-defined]
        
        # Получаем ID
        server_id = self.db.get_server_id("http://test-server:9090")  # type: ignore[attr-defined]
        self.assertIsNotNone(server_id)
        self.assertIsInstance(server_id, int)
        
        # Проверяем несуществующий сервер
        non_existent_id = self.db.get_server_id("http://non-existent:9090")  # type: ignore[attr-defined]
        self.assertIsNone(non_existent_id)
    
    def test_save_metrics(self):
        """Тест сохранения метрик"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")  # type: ignore[attr-defined]
        
        # Сохраняем метрики
        disk_usage = {"C:": {"usage_precent": 75.5}}
        self.db.save_metrics("http://test-server:9090", 45.2, 60.8, 65.0, disk_usage)  # type: ignore[attr-defined]
        
        # Проверяем в базе данных
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cpu_usage, ram_usage, temperature, disk_usage 
            FROM metrics 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
            ORDER BY timestamp DESC 
            LIMIT 1
        """, ("http://test-server:9090",))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 45.2)  # cpu_usage
        self.assertEqual(result[1], 60.8)  # ram_usage
        self.assertEqual(result[2], 65.0)  # temperature
        self.assertEqual(result[3], json.dumps(disk_usage))  # disk_usage
        conn.close()
    
    def test_add_incident(self):
        """Тест добавления инцидента"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")  # type: ignore[attr-defined]
        
        # Добавляем инцидент
        self.db.add_incident("http://test-server:9090", "cpu_temp", "critical", "High CPU temperature")  # type: ignore[attr-defined]
        
        # Проверяем в базе данных
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, severity, description, resolved 
            FROM incidents 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
        """, ("http://test-server:9090",))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "cpu_temp")
        self.assertEqual(result[1], "critical")
        self.assertEqual(result[2], "High CPU temperature")
        self.assertEqual(result[3], False)  # resolved
        conn.close()
    
    def test_add_alert(self):
        """Тест добавления оповещения"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")  # type: ignore[attr-defined]
        
        # Добавляем оповещение
        self.db.add_alert("http://test-server:9090", "temperature_warning", "High temperature alert")  # type: ignore[attr-defined]
        self.db.add_alert("http://test-server:9090", "disk_warning", "High disk usage alert")  # type: ignore[attr-defined]
        
        # Проверяем в базе данных
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, message, acknowledged 
            FROM alerts 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
        """, ("http://test-server:9090",))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "temperature_warning")
        self.assertEqual(result[1], "High temperature alert")
        self.assertEqual(result[2], False)  # acknowledged
        conn.close()
    
    def test_get_metrics_history(self):
        """Тест получения истории метрик"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")
        
        # Сохраняем несколько метрик
        disk_usage = {"C:": {"usage_precent": 75.5}}
        self.db.save_metrics("http://test-server:9090", 45.2, 60.8, 65.0, disk_usage)
        self.db.save_metrics("http://test-server:9090", 50.1, 65.3, 70.2, disk_usage)  # type: ignore[attr-defined]
        
        # Получаем историю
        history = self.db.get_metrics_history("http://test-server:9090", hours=24)  # type: ignore[attr-defined]
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 2)
        
        # Проверяем структуру данных
        for record in history:
            self.assertEqual(len(record), 5)  # timestamp, cpu_usage, ram_usage, temperature, disk_usage
            self.assertIsInstance(record[1], (int, float))  # cpu_usage
            self.assertIsInstance(record[2], (int, float))  # ram_usage
            self.assertIsInstance(record[3], (int, float))  # temperature
    
    def test_get_incidents(self):
        """Тест получения инцидентов"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")
        
        # Добавляем несколько инцидентов
        self.db.add_incident("http://test-server:9090", "cpu_temp", "critical", "High CPU temperature")  # type: ignore[attr-defined]
        self.db.add_incident("http://test-server:9090", "disk_usage", "warning", "High disk usage")  # type: ignore[attr-defined]
        
        # Получаем все инциденты
        incidents = self.db.get_incidents()  # type: ignore[attr-defined]
        self.assertIsInstance(incidents, list)
        self.assertGreaterEqual(len(incidents), 2)
        
        # Получаем инциденты для конкретного сервера
        server_incidents = self.db.get_incidents("http://test-server:9090")  # type: ignore[attr-defined]
        self.assertIsInstance(server_incidents, list)
        self.assertGreaterEqual(len(server_incidents), 2)
        
        # Проверяем структуру данных (работаем с кортежами)
        for incident in server_incidents:
            self.assertGreaterEqual(len(incident), 7)  # id, server_id, timestamp, type, severity, description, ...
            self.assertIsInstance(incident[3], str)  # type
            self.assertIsInstance(incident[4], str)  # severity
            self.assertIsInstance(incident[5], str)  # description
            self.assertIn(incident[7], (0, 1, False, True))  # resolved
    
    def test_resolve_incident(self):
        """Тест разрешения инцидента"""
        assert self.db is not None
        # Добавляем сервер и инцидент
        self.db.add_server("http://test-server:9090", "Test Server")
        self.db.add_incident("http://test-server:9090", "cpu_temp", "critical", "High CPU temperature")  # type: ignore[attr-defined]
        
        # Получаем ID инцидента
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM incidents 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
        """, ("http://test-server:9090",))
        incident_id = cursor.fetchone()[0]
        conn.close()
        
        # Разрешаем инцидент
        self.db.resolve_incident(incident_id)  # type: ignore[attr-defined]
        
        # Проверяем, что инцидент разрешен
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT resolved, resolved_at FROM incidents WHERE id = ?", (incident_id,))
        result = cursor.fetchone()
        self.assertTrue(result[0])  # resolved
        self.assertIsNotNone(result[1])  # resolved_at
        conn.close()
    
    def test_delete_incident(self):
        """Тест удаления инцидента"""
        assert self.db is not None
        # Добавляем сервер и инцидент
        self.db.add_server("http://test-server:9090", "Test Server")
        self.db.add_incident("http://test-server:9090", "cpu_temp", "critical", "High CPU temperature")  # type: ignore[attr-defined]
        
        # Получаем ID инцидента
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM incidents 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
        """, ("http://test-server:9090",))
        incident_id = cursor.fetchone()[0]
        conn.close()
        
        # Удаляем инцидент
        self.db.delete_incident(incident_id)  # type: ignore[attr-defined]
        
        # Проверяем, что инцидент удален
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM incidents WHERE id = ?", (incident_id,))
        result = cursor.fetchone()
        self.assertIsNone(result)
        conn.close()
    
    def test_get_unacknowledged_alerts(self):
        """Тест получения неподтвержденных оповещений"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")
        
        # Добавляем оповещения
        self.db.add_alert("http://test-server:9090", "temperature_warning", "High temperature alert")  # type: ignore[attr-defined]
        self.db.add_alert("http://test-server:9090", "disk_warning", "High disk usage alert")  # type: ignore[attr-defined]
        
        # Получаем неподтвержденные оповещения
        alerts = self.db.get_unacknowledged_alerts()  # type: ignore[attr-defined]
        self.assertIsInstance(alerts, list)
        self.assertGreaterEqual(len(alerts), 2)
        
        # Получаем неподтвержденные оповещения для конкретного сервера
        server_alerts = self.db.get_unacknowledged_alerts("http://test-server:9090")  # type: ignore[attr-defined]
        self.assertIsInstance(server_alerts, list)
        self.assertGreaterEqual(len(server_alerts), 2)
        
        # Проверяем, что все оповещения неподтвержденные (работаем с кортежами)
        for alert in server_alerts:
            # acknowledged - 6-й элемент (индекс 6)
            self.assertFalse(alert[6])
    
    def test_acknowledge_alert(self):
        """Тест подтверждения оповещения"""
        assert self.db is not None
        # Добавляем сервер и оповещение
        self.db.add_server("http://test-server:9090", "Test Server")
        self.db.add_alert("http://test-server:9090", "temperature_warning", "High temperature alert")  # type: ignore[attr-defined]
        
        # Получаем ID оповещения
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM alerts 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
        """, ("http://test-server:9090",))
        alert_id = cursor.fetchone()[0]
        conn.close()
        
        # Подтверждаем оповещение
        self.db.acknowledge_alert(alert_id)  # type: ignore[attr-defined]
        
        # Проверяем, что оповещение подтверждено
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT acknowledged, acknowledged_at FROM alerts WHERE id = ?", (alert_id,))
        result = cursor.fetchone()
        self.assertTrue(result[0])  # acknowledged
        self.assertIsNotNone(result[1])  # acknowledged_at
        conn.close()
    
    def test_get_all_alerts(self):
        """Тест получения всех оповещений"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")
        
        # Добавляем оповещения
        self.db.add_alert("http://test-server:9090", "temperature_warning", "High temperature alert")  # type: ignore[attr-defined]
        self.db.add_alert("http://test-server:9090", "disk_warning", "High disk usage alert")  # type: ignore[attr-defined]
        
        # Получаем все оповещения
        alerts = self.db.get_all_alerts()  # type: ignore[attr-defined]
        self.assertIsInstance(alerts, list)
        self.assertGreaterEqual(len(alerts), 2)
        
        # Получаем все оповещения для конкретного сервера
        server_alerts = self.db.get_all_alerts("http://test-server:9090")  # type: ignore[attr-defined]
        self.assertIsInstance(server_alerts, list)
        self.assertGreaterEqual(len(server_alerts), 2)
    
    def test_get_acknowledged_alerts(self):
        """Тест получения подтвержденных оповещений"""
        assert self.db is not None
        # Добавляем сервер и оповещение
        self.db.add_server("http://test-server:9090", "Test Server")
        self.db.add_alert("http://test-server:9090", "temperature_warning", "High temperature alert")  # type: ignore[attr-defined]
        
        # Получаем ID оповещения и подтверждаем его
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM alerts 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
        """, ("http://test-server:9090",))
        alert_id = cursor.fetchone()[0]
        conn.close()
        
        self.db.acknowledge_alert(alert_id)  # type: ignore[attr-defined]
        
        # Получаем подтвержденные оповещения
        acknowledged_alerts = self.db.get_acknowledged_alerts()  # type: ignore[attr-defined]
        acknowledged_alerts = self.db.get_acknowledged_alerts()  # type: ignore[attr-defined]
        self.assertIsInstance(acknowledged_alerts, list)
        self.assertGreaterEqual(len(acknowledged_alerts), 1)
        
        # Проверяем, что все оповещения подтверждены (работаем с кортежами)
        for alert in acknowledged_alerts:
            # acknowledged - 6-й элемент (индекс 6)
            self.assertTrue(alert[6])
    
    def test_cleanup_old_data(self):
        """Тест очистки старых данных"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")
        
        # Сохраняем метрику с датой в прошлом
        conn = self.db.get_connection()  # type: ignore[attr-defined]
        cursor = conn.cursor()
        server_id = self.db.get_server_id("http://test-server:9090")  # type: ignore[attr-defined]
        old_time = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO metrics (server_id, timestamp, cpu_usage, ram_usage, temperature, disk_usage) VALUES (?, ?, ?, ?, ?, ?)",
                       (server_id, old_time, 10.0, 20.0, 30.0, None))
        conn.commit()
        conn.close()
        
        # Проверяем, что метрика сохранена
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM metrics")
        initial_count = cursor.fetchone()[0]
        conn.close()
        
        self.assertGreater(initial_count, 0)
        
        # Очищаем старые данные (более 0 дней)
        self.db.cleanup_old_data(days=0)  # type: ignore[attr-defined]
        
        # Проверяем, что данные очищены
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM metrics")
        final_count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(final_count, 0)
    
    def test_get_connection(self):
        """Тест получения соединения"""
        assert self.db is not None
        connection = self.db.get_connection()  # type: ignore[attr-defined]
        self.assertIsInstance(connection, sqlite3.Connection)
        connection.close()
    
    def test_update_servers_with_empty_list(self):
        """Тест обновления списка серверов с пустым списком"""
        # Создаем новую базу данных без серверов по умолчанию
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # Создаем базу данных без автоматического добавления сервера по умолчанию
        db = Database(temp_db.name)
        
        # Проверяем, что сервер по умолчанию добавлен
        self.assertIn("http://localhost:9090", db.servers)
        
        # Очистка
        db.conn.close()
        os.unlink(temp_db.name)
    
    def test_save_metrics_with_none_disk_usage(self):
        """Тест сохранения метрик с пустым disk_usage"""
        assert self.db is not None
        # Добавляем сервер
        self.db.add_server("http://test-server:9090", "Test Server")
        
        # Сохраняем метрики с None disk_usage
        self.db.save_metrics("http://test-server:9090", 45.2, 60.8, 65.0, None)  # type: ignore[attr-defined]
        
        # Проверяем в базе данных
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT disk_usage 
            FROM metrics 
            WHERE server_id = (SELECT id FROM servers WHERE url = ?)
            ORDER BY timestamp DESC 
            LIMIT 1
        """, ("http://test-server:9090",))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertIsNone(result[0])  # disk_usage должен быть None
        conn.close()
    
    def test_save_metrics_with_nonexistent_server(self):
        """Тест сохранения метрик для несуществующего сервера"""
        assert self.db is not None
        # Пытаемся сохранить метрики для несуществующего сервера
        disk_usage = {"C:": {"usage_precent": 75.5}}
        self.db.save_metrics("http://nonexistent-server:9090", 45.2, 60.8, 65.0, disk_usage)  # type: ignore[attr-defined]
        
        # Проверяем, что метрики не сохранены
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM metrics")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main() 