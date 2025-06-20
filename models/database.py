import sqlite3 
import datetime
import threading

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_database()
        self.update_servers()

    def get_connection(self):
        """Создает новое соединение для использования в других потоках"""
        return sqlite3.connect(self.db_file)

    def create_database(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )""")

        # Таблица метрик (расширенная)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_usage REAL,
                ram_usage REAL,
                temperature REAL,
                disk_usage TEXT,  -- JSON для хранения данных по дискам
                FOREIGN KEY(server_id) REFERENCES servers(id)
            )""")

        # Таблица инцидентов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT,  -- 'cpu_temp', 'disk_usage', 'ram_usage'
                severity TEXT,  -- 'warning', 'critical'
                description TEXT,
                resolved_at DATETIME,
                resolved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY(server_id) REFERENCES servers(id)
            )""")

        # Таблица оповещений
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT,
                message TEXT,
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_at DATETIME,
                FOREIGN KEY(server_id) REFERENCES servers(id)
            )""")

        # Индексы для оптимизации запросов
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_server ON metrics(server_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_server ON incidents(server_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        
        self.conn.commit()

    def _refresh_servers_list(self):
        """Обновляет список серверов (внутренний метод)"""
        self.servers = []
        self.cursor.execute("SELECT url FROM servers")
        rows = self.cursor.fetchall()
        for row in rows:
            self.servers.append(row[0])

    def update_servers(self):
        with self._lock:
            self._refresh_servers_list()
            if not self.servers:
                # Добавляем сервер по умолчанию напрямую, без рекурсивного вызова
                self.cursor.execute("INSERT OR REPLACE INTO servers (url) VALUES (?)", ("http://localhost:9090",))
                self.conn.commit()
                self._refresh_servers_list()

    def add_server(self, url, name=None):
        try:
            with self._lock:
                if name is None:
                    name = url
                self.cursor.execute("INSERT OR REPLACE INTO servers (url) VALUES (?)", (url,))
                self.conn.commit()
                # Обновляем список серверов без рекурсивного вызова
                self._refresh_servers_list()
        except Exception as e:
            print(f"Error adding server: {e}")

    def delete_server(self, url):
        with self._lock:
            self.cursor.execute("DELETE FROM servers WHERE url = ?", (url,))
            self.conn.commit()
            # Обновляем список серверов без рекурсивного вызова
            self._refresh_servers_list()

    def get_server_id(self, url):
        with self._lock:
            self.cursor.execute("SELECT id FROM servers WHERE url = ?", (url,))
            result = self.cursor.fetchone()
            return result[0] if result else None

    def get_server_id_threadsafe(self, url, cursor):
        """Потокобезопасное получение ID сервера"""
        cursor.execute("SELECT id FROM servers WHERE url = ?", (url,))
        result = cursor.fetchone()
        return result[0] if result else None

    def save_metrics(self, server_url, cpu_usage, ram_usage, temperature, disk_usage):
        """Сохраняет метрики в базу данных (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            server_id = self.get_server_id_threadsafe(server_url, cursor)
            if server_id:
                import json
                disk_usage_json = json.dumps(disk_usage) if disk_usage else None
                # Явно указываем текущее время при сохранении
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO metrics (server_id, timestamp, cpu_usage, ram_usage, temperature, disk_usage)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (server_id, current_time, cpu_usage, ram_usage, temperature, disk_usage_json))
                conn.commit()
        finally:
            conn.close()

    def get_metrics_history(self, server_url, hours=24):
        """Получает историю метрик за указанное количество часов (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            server_id = self.get_server_id_threadsafe(server_url, cursor)
            if not server_id:
                return []
            
            # Вычисляем время начала периода
            start_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT timestamp, cpu_usage, ram_usage, temperature, disk_usage
                FROM metrics 
                WHERE server_id = ? AND timestamp >= ?
                ORDER BY timestamp
            """, (server_id, start_time_str))
            
            return cursor.fetchall()
        finally:
            conn.close()

    def add_incident(self, server_url, incident_type, severity, description):
        """Добавляет новый инцидент (потокобезопасно)"""
        import datetime
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            server_id = self.get_server_id_threadsafe(server_url, cursor)
            if server_id:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO incidents (server_id, type, severity, description, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (server_id, incident_type, severity, description, now))
                conn.commit()
        finally:
            conn.close()

    def get_incidents(self, server_url=None, limit=100):
        """Получает список инцидентов (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if server_url:
                server_id = self.get_server_id_threadsafe(server_url, cursor)
                cursor.execute("""
                    SELECT i.*, s.url as server_name
                    FROM incidents i
                    JOIN servers s ON i.server_id = s.id
                    WHERE i.server_id = ?
                    ORDER BY i.timestamp DESC
                    LIMIT ?
                """, (server_id, limit))
            else:
                cursor.execute("""
                    SELECT i.*, s.url as server_name
                    FROM incidents i
                    JOIN servers s ON i.server_id = s.id
                    ORDER BY i.timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            return cursor.fetchall()
        finally:
            conn.close()

    def resolve_incident(self, incident_id):
        """Отмечает инцидент как разрешенный (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE incidents 
                SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (incident_id,))
            conn.commit()
        finally:
            conn.close()

    def delete_incident(self, incident_id):
        """Удаляет инцидент из базы данных (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
            conn.commit()
        finally:
            conn.close()

    def add_alert(self, server_url, alert_type, message):
        """Добавляет новое оповещение (потокобезопасно)"""
        import datetime
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            server_id = self.get_server_id_threadsafe(server_url, cursor)
            if server_id:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO alerts (server_id, type, message, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (server_id, alert_type, message, now))
                conn.commit()
        finally:
            conn.close()

    def get_unacknowledged_alerts(self, server_url=None):
        """Получает неподтвержденные оповещения (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if server_url:
                server_id = self.get_server_id_threadsafe(server_url, cursor)
                cursor.execute("""
                    SELECT a.*, s.url as server_name
                    FROM alerts a
                    JOIN servers s ON a.server_id = s.id
                    WHERE a.server_id = ? AND a.acknowledged = FALSE
                    ORDER BY a.timestamp DESC
                """, (server_id,))
            else:
                cursor.execute("""
                    SELECT a.*, s.url as server_name
                    FROM alerts a
                    JOIN servers s ON a.server_id = s.id
                    WHERE a.acknowledged = FALSE
                    ORDER BY a.timestamp DESC
                """)
            
            return cursor.fetchall()
        finally:
            conn.close()

    def acknowledge_alert(self, alert_id):
        """Подтверждает оповещение (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alerts 
                SET acknowledged = TRUE, acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (alert_id,))
            conn.commit()
        finally:
            conn.close()

    def get_all_alerts(self, server_url=None):
        """Получает все оповещения (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if server_url:
                server_id = self.get_server_id_threadsafe(server_url, cursor)
                cursor.execute("""
                    SELECT a.*, s.url as server_name
                    FROM alerts a
                    JOIN servers s ON a.server_id = s.id
                    WHERE a.server_id = ?
                    ORDER BY a.timestamp DESC
                """, (server_id,))
            else:
                cursor.execute("""
                    SELECT a.*, s.url as server_name
                    FROM alerts a
                    JOIN servers s ON a.server_id = s.id
                    ORDER BY a.timestamp DESC
                """)
            
            return cursor.fetchall()
        finally:
            conn.close()

    def get_acknowledged_alerts(self, server_url=None):
        """Получает подтвержденные оповещения (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if server_url:
                server_id = self.get_server_id_threadsafe(server_url, cursor)
                cursor.execute("""
                    SELECT a.*, s.url as server_name
                    FROM alerts a
                    JOIN servers s ON a.server_id = s.id
                    WHERE a.server_id = ? AND a.acknowledged = TRUE
                    ORDER BY a.timestamp DESC
                """, (server_id,))
            else:
                cursor.execute("""
                    SELECT a.*, s.url as server_name
                    FROM alerts a
                    JOIN servers s ON a.server_id = s.id
                    WHERE a.acknowledged = TRUE
                    ORDER BY a.timestamp DESC
                """)
            
            return cursor.fetchall()
        finally:
            conn.close()

    def cleanup_old_data(self, days=30):
        """Удаляет старые данные для экономии места (потокобезопасно)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Удаляем старые метрики
            cursor.execute("DELETE FROM metrics WHERE timestamp < datetime('now', '-{} days')".format(days))
            metrics_deleted = cursor.rowcount
            
            # Удаляем старые разрешенные инциденты
            cursor.execute("DELETE FROM incidents WHERE resolved = TRUE AND timestamp < datetime('now', '-{} days')".format(days))
            incidents_deleted = cursor.rowcount
            
            # Удаляем старые подтвержденные оповещения
            cursor.execute("DELETE FROM alerts WHERE acknowledged = TRUE AND timestamp < datetime('now', '-{} days')".format(days))
            alerts_deleted = cursor.rowcount
            
            conn.commit()
            
            print(f"Очистка данных: удалено {metrics_deleted} метрик, {incidents_deleted} инцидентов, {alerts_deleted} оповещений")
            
            return {
                'metrics_deleted': metrics_deleted,
                'incidents_deleted': incidents_deleted,
                'alerts_deleted': alerts_deleted
            }
            
        except Exception as e:
            print(f"Ошибка при очистке данных: {e}")
            raise
        finally:
            conn.close()