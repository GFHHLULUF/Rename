import customtkinter as ctk
import datetime

class IncidentsTab:
    def __init__(self, parent, database):
        self.parent = parent
        self.db = database
        
        self.setup_ui()
        self.refresh_incidents()

    def setup_ui(self):
        """Настройка интерфейса"""
        # Верхняя панель управления
        self.control_frame = ctk.CTkFrame(self.parent)
        self.control_frame.pack(fill=ctk.X, padx=10, pady=5)
        
        # Кнопка обновления
        self.refresh_button = ctk.CTkButton(
            self.control_frame, 
            text="Обновить", 
            command=self.refresh_incidents,
            width=100
        )
        self.refresh_button.pack(side=ctk.LEFT, padx=10, pady=5)
        
        # Кнопка очистки старых данных
        '''self.cleanup_button = ctk.CTkButton(
            self.control_frame, 
            text="Очистить старые данные", 
            command=self.cleanup_old_data,
            width=150
        )
        self.cleanup_button.pack(side=ctk.LEFT, padx=10, pady=5)'''
        
        # Статистика
        self.stats_label = ctk.CTkLabel(self.control_frame, text="", font=("Arial", 12))
        self.stats_label.pack(side=ctk.RIGHT, padx=10, pady=5)
        
        # Основной контейнер для инцидентов
        self.main_container = ctk.CTkScrollableFrame(self.parent)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        
        # Заголовки таблицы
        self.setup_table_headers()
        
        # Контейнер для инцидентов
        self.incidents_container = ctk.CTkFrame(self.main_container)
        self.incidents_container.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        
        self.incidents_list = []

    def setup_table_headers(self):
        """Настройка заголовков таблицы"""
        headers_frame = ctk.CTkFrame(self.main_container)
        headers_frame.pack(fill=ctk.X, padx=5, pady=2)
        
        # Настройка колонок
        headers_frame.grid_columnconfigure(0, weight=1)  # Время
        headers_frame.grid_columnconfigure(1, weight=1)  # Сервер
        headers_frame.grid_columnconfigure(2, weight=1)  # Тип
        headers_frame.grid_columnconfigure(3, weight=2)  # Описание
        headers_frame.grid_columnconfigure(4, weight=1)  # Статус
        headers_frame.grid_columnconfigure(5, weight=1)  # Действия
        
        # Заголовки
        headers = ["Время", "Сервер", "Тип", "Описание", "Статус", "Действия"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, font=("Arial", 12, "bold"))
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

    def refresh_incidents(self):
        """Обновление списка инцидентов"""
        # Очищаем старые инциденты
        for incident_widget in self.incidents_list:
            incident_widget.destroy()
        self.incidents_list.clear()
        
        # Получаем инциденты
        incidents = self.db.get_incidents(limit=100)
        
        if not incidents:
            no_incidents_label = ctk.CTkLabel(
                self.incidents_container, 
                text="Нет инцидентов", 
                font=("Arial", 14)
            )
            no_incidents_label.pack(expand=True)
            self.incidents_list.append(no_incidents_label)
            self.update_stats(incidents)
            return
        
        # Создаем строки для каждого инцидента
        for i, incident in enumerate(incidents):
            self.create_incident_row(incident, i + 1)
        
        self.update_stats(incidents)

    def create_incident_row(self, incident, row_num):
        """Создание строки инцидента"""
        # incident: (id, server_id, timestamp, type, severity, description, resolved_at, resolved, server_name)
        
        row_frame = ctk.CTkFrame(self.incidents_container)
        row_frame.pack(fill=ctk.X, padx=5, pady=2)
        
        # Настройка колонок
        row_frame.grid_columnconfigure(0, weight=1)  # Время
        row_frame.grid_columnconfigure(1, weight=1)  # Сервер
        row_frame.grid_columnconfigure(2, weight=1)  # Тип
        row_frame.grid_columnconfigure(3, weight=2)  # Описание
        row_frame.grid_columnconfigure(4, weight=1)  # Статус
        row_frame.grid_columnconfigure(5, weight=1)  # Действия
        
        # Время
        timestamp_str = incident[2]  # timestamp
        try:
            # Парсим SQLite timestamp
            if timestamp_str:
                # Пробуем разные форматы времени
                formats = [
                    '%Y-%m-%d %H:%M:%S',  # Стандартный SQLite формат
                    '%Y-%m-%d %H:%M:%S.%f',  # С микросекундами
                    '%Y-%m-%dT%H:%M:%S',  # ISO формат без Z
                    '%Y-%m-%dT%H:%M:%S.%f',  # ISO формат с микросекундами
                    '%Y-%m-%dT%H:%M:%SZ',  # ISO формат с Z
                    '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO формат с микросекундами и Z
                ]
                
                dt = None
                for fmt in formats:
                    try:
                        dt = datetime.datetime.strptime(timestamp_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if dt:
                    time_display = dt.strftime("%d.%m.%Y %H:%M:%S")
                else:
                    time_display = str(timestamp_str)
            else:
                time_display = "Н/Д"
        except Exception as e:
            print(f"Ошибка парсинга времени '{timestamp_str}': {e}")
            time_display = str(timestamp_str) if timestamp_str else "Н/Д"
        
        time_label = ctk.CTkLabel(row_frame, text=time_display, font=("Arial", 11))
        time_label.grid(row=0, column=0, padx=5, pady=3, sticky="ew")
        
        # Сервер
        server_name = incident[8] if incident[8] else f"Сервер {incident[1]}"  # server_name (теперь это URL)
        server_label = ctk.CTkLabel(row_frame, text=server_name, font=("Arial", 11))
        server_label.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        
        # Тип
        incident_type = incident[3]  # type
        type_display = self.get_type_display_name(incident_type) or str(incident_type) or "Неизвестно"
        type_label = ctk.CTkLabel(row_frame, text=type_display, font=("Arial", 11))
        type_label.grid(row=0, column=2, padx=5, pady=3, sticky="ew")
        
        # Описание
        description = incident[5]  # description
        desc_label = ctk.CTkLabel(row_frame, text=description, font=("Arial", 11), wraplength=300)
        desc_label.grid(row=0, column=3, padx=5, pady=3, sticky="ew")
        
        # Статус
        resolved = incident[7]  # resolved
        if resolved:
            status_text = "Разрешен"
            status_color = "#a8e4a0"
            if incident[6]:  # resolved_at
                try:
                    # Парсим SQLite timestamp для resolved_at
                    resolved_timestamp_str = incident[6]
                    if resolved_timestamp_str:
                        formats = [
                            '%Y-%m-%d %H:%M:%S',  # Стандартный SQLite формат
                            '%Y-%m-%d %H:%M:%S.%f',  # С микросекундами
                            '%Y-%m-%dT%H:%M:%S',  # ISO формат без Z
                            '%Y-%m-%dT%H:%M:%S.%f',  # ISO формат с микросекундами
                            '%Y-%m-%dT%H:%M:%SZ',  # ISO формат с Z
                            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO формат с микросекундами и Z
                        ]
                        
                        resolved_dt = None
                        for fmt in formats:
                            try:
                                resolved_dt = datetime.datetime.strptime(resolved_timestamp_str, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if resolved_dt:
                            status_text += f"\n{resolved_dt.strftime('%d.%m.%Y %H:%M:%S')}"
                        else:
                            status_text += f"\n{str(resolved_timestamp_str)}"
                except Exception as e:
                    print(f"Ошибка парсинга времени разрешения '{incident[6]}': {e}")
        else:
            status_text = "Активен"
            status_color = "#FF6D6A"
        
        status_label = ctk.CTkLabel(row_frame, text=status_text, text_color=status_color, font=("Arial", 11))
        status_label.grid(row=0, column=4, padx=5, pady=3, sticky="ew")
        
        # Действия
        actions_frame = ctk.CTkFrame(row_frame)
        actions_frame.grid(row=0, column=5, padx=5, pady=3, sticky="ew")
        
        if not resolved:
            resolve_button = ctk.CTkButton(
                actions_frame, 
                text="Разрешить", 
                command=lambda inc_id=incident[0]: self.resolve_incident(inc_id),
                width=80,
                height=25
            )
            resolve_button.pack(fill=ctk.BOTH, padx=2)
        else:
            # Для разрешенных инцидентов показываем кнопку удаления
            delete_button = ctk.CTkButton(
                actions_frame, 
                text="Удалить", 
                command=lambda inc_id=incident[0]: self.delete_incident(inc_id),
                width=80,
                height=25,
                fg_color="#FF6D6A",  # Красный цвет для кнопки удаления
                hover_color="#FF4444"
            )
            delete_button.pack(fill=ctk.BOTH, padx=2)
        
        # Цвет фона в зависимости от серьезности
        severity = incident[4]  # severity
        if severity == "critical":
            row_frame.configure(fg_color="#4a2b2b")  # Темно-красный для критических
        elif severity == "warning":
            row_frame.configure(fg_color="#4a4a2b")  # Темно-желтый для предупреждений
        
        self.incidents_list.append(row_frame)

    def get_type_display_name(self, incident_type):
        """Получение отображаемого имени типа инцидента"""
        type_names = {
            "cpu_temp": "Температура CPU",
            "disk_usage": "Использование диска",
            "ram_usage": "Использование RAM"
        }
        return type_names.get(incident_type, incident_type)

    def resolve_incident(self, incident_id):
        """Разрешение инцидента"""
        self.db.resolve_incident(incident_id)
        self.refresh_incidents()

    def delete_incident(self, incident_id):
        """Удаление инцидента"""
        self.db.delete_incident(incident_id)
        self.refresh_incidents()

    def update_stats(self, incidents):
        """Обновление статистики"""
        if not incidents:
            self.stats_label.configure(text="Всего инцидентов: 0")
            return
        
        total = len(incidents)
        active = sum(1 for inc in incidents if not inc[7])  # resolved
        resolved = total - active
        
        critical = sum(1 for inc in incidents if inc[4] == "critical")  # severity
        warning = sum(1 for inc in incidents if inc[4] == "warning")
        
        stats_text = f"Всего: {total} | Активных: {active} | Разрешенных: {resolved} | Критических: {critical} | Предупреждений: {warning}"
        self.stats_label.configure(text=stats_text)

    def cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            # Показываем сообщение о начале очистки
            self.stats_label.configure(text="Очистка данных...")
            
            # Выполняем очистку
            result = self.db.cleanup_old_data(days=30)
            
            # Показываем результат
            metrics = result.get('metrics_deleted', 0)
            incidents = result.get('incidents_deleted', 0)
            alerts = result.get('alerts_deleted', 0)
            
            result_text = f"Очищено: {metrics} метрик, {incidents} инцидентов, {alerts} оповещений"
            self.stats_label.configure(text=result_text)
            
            # Обновляем список инцидентов
            self.refresh_incidents()
            
            # Через 3 секунды возвращаем обычную статистику
            self.parent.after(3000, lambda: self.update_stats(self.db.get_incidents(limit=100)))
            
        except Exception as e:
            # Показываем ошибку
            error_text = f"Ошибка очистки: {str(e)}"
            self.stats_label.configure(text=error_text)
            print(f"Ошибка при очистке данных: {e}")
            
            # Через 5 секунд возвращаем обычную статистику
            self.parent.after(5000, lambda: self.update_stats(self.db.get_incidents(limit=100))) 