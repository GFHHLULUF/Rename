import datetime
import threading
import time
from collections import defaultdict

class AlertManager:
    def __init__(self, database):
        self.db = database
        self.temperature_alerts = defaultdict(list)  # server_url -> list of timestamps
        self.disk_alerts = defaultdict(set)  # server_url -> set of disk volumes
        self.ram_alerts = defaultdict(bool)  # server_url -> bool
        self.alert_lock = threading.Lock()

    def check_alerts(self, server_url, cpu_info, ram_info, rom_info):
        """Проверяет все условия для оповещений"""
        with self.alert_lock:
            self._check_temperature_alert(server_url, cpu_info)
            self._check_disk_usage_alert(server_url, rom_info)
            self._check_ram_usage_alert(server_url, ram_info)

    def _check_temperature_alert(self, server_url, cpu_info):
        """Проверяет температуру процессора"""
        if not cpu_info or 'temperatur' not in cpu_info:
            return

        temperature = float(cpu_info['temperatur'])
        current_time = datetime.datetime.now()

        if temperature > 85:
            # Добавляем время в список
            self.temperature_alerts[server_url].append(current_time)
            
            # Удаляем записи старше 10 минут
            cutoff_time = current_time - datetime.timedelta(minutes=10)
            self.temperature_alerts[server_url] = [
                t for t in self.temperature_alerts[server_url] 
                if t > cutoff_time
            ]

            # Если температура высокая более 10 минут
            if len(self.temperature_alerts[server_url]) >= 2:  # 2 записи = 10 минут (при обновлении каждые 5 сек)
                alert_message = f"КРИТИЧЕСКОЕ ОПОВЕЩЕНИЕ: Температура процессора {temperature:.1f}°C превышает 85°C более 10 минут!"
                self.db.add_alert(server_url, "temperature_critical", alert_message)
                self.db.add_incident(server_url, "cpu_temp", "critical", 
                                   f"Температура процессора {temperature:.1f}°C превышает 85°C более 10 минут")
            else:
                alert_message = f"ПРЕДУПРЕЖДЕНИЕ: Температура процессора {temperature:.1f}°C превышает 85°C"
                self.db.add_alert(server_url, "temperature_warning", alert_message)
        else:
            # Сбрасываем счетчик если температура нормальная
            self.temperature_alerts[server_url].clear()

    def _check_disk_usage_alert(self, server_url, rom_info):
        """Проверяет использование дисков"""
        if not rom_info:
            return

        current_alerts = set()
        for volume, disk_data in rom_info.items():
            usage_percent = float(disk_data['usage_precent'])
            
            if usage_percent > 90:
                current_alerts.add(volume)
                
                # Проверяем, не было ли уже оповещения для этого диска
                if volume not in self.disk_alerts[server_url]:
                    alert_message = f"ПРЕДУПРЕЖДЕНИЕ: Диск {volume} заполнен на {usage_percent:.1f}%"
                    self.db.add_alert(server_url, "disk_usage", alert_message)
                    self.db.add_incident(server_url, "disk_usage", "warning", 
                                       f"Диск {volume} заполнен на {usage_percent:.1f}%")
                    self.disk_alerts[server_url].add(volume)

        # Удаляем диски, которые больше не превышают лимит
        self.disk_alerts[server_url] = self.disk_alerts[server_url].intersection(current_alerts)

    def _check_ram_usage_alert(self, server_url, ram_info):
        """Проверяет использование RAM"""
        if not ram_info or 'usage_precent' not in ram_info:
            return

        ram_usage = float(ram_info['usage_precent'])
        
        if ram_usage > 90:
            if not self.ram_alerts[server_url]:
                alert_message = f"ПРЕДУПРЕЖДЕНИЕ: Использование RAM {ram_usage:.1f}% превышает 90%"
                self.db.add_alert(server_url, "ram_usage", alert_message)
                self.db.add_incident(server_url, "ram_usage", "warning", 
                                   f"Использование RAM {ram_usage:.1f}% превышает 90%")
                self.ram_alerts[server_url] = True
        else:
            self.ram_alerts[server_url] = False

    def get_active_alerts(self, server_url=None):
        """Получает активные оповещения"""
        return self.db.get_unacknowledged_alerts(server_url)

    def acknowledge_alert(self, alert_id):
        """Подтверждает оповещение"""
        self.db.acknowledge_alert(alert_id) 