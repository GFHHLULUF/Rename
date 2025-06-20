import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import datetime
from models.monitor import PrometheusMonitor
from models.database import Database
from models.alert_manager import AlertManager
from views.servers_window import ServersWindow
from views.current_status_tab import CurrentStatusTab
from views.history_graphs_tab import HistoryGraphsTab
from views.incidents_tab import IncidentsTab

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.DBname = "servers.db"
        
        # Настройка темной темы для главного окна
        self.configure(fg_color="#1a1a1a")  # Очень темный фон
        
        self.db = Database(self.DBname)
        self.servers = self.db.servers
        self.alert_manager = AlertManager(self.db)

        self.title("Мониторинг серверов")
        self.geometry("1200x800+400+100")
        self.minsize(1000, 600)

        self.setup_connection_frame()
        self.selected_url = self.connectionEntry.get() if self.connectionEntry.get() else ""
        
        # Инициализируем монитор с обработкой ошибок
        try:
            self.monitor = PrometheusMonitor(self.selected_url)
        except Exception as e:
            print(f"Ошибка при инициализации монитора: {e}")
            self.monitor = None

        self.setup_tabs()

    def setup_connection_frame(self):
        """Настройка фрейма подключения"""
        self.connectionFrame = ctk.CTkFrame(self, fg_color="#2d2d2d")  # Темный фон для фрейма
        self.connectionFrame.pack(pady=10)
        self.show_connection()

    def setup_alerts_frame(self):
        """Настройка фрейма оповещений под Tabview"""
        self.alerts_frame = ctk.CTkFrame(self, fg_color="#2d2d2d")  # Темный фон для фрейма
        self.alerts_frame.pack(fill=ctk.X, padx=10, pady=5)
        
        self.alerts_label = ctk.CTkLabel(self.alerts_frame, text="Активные оповещения:", 
                                        font=("Arial", 16, "bold"), text_color="#ffffff")
        self.alerts_label.pack(anchor='w', padx=10, pady=5)
        
        self.alerts_container = ctk.CTkFrame(self.alerts_frame, fg_color="#1a1a1a")  # Еще более темный фон
        self.alerts_container.pack(fill=ctk.X, padx=10, pady=5)
        
        self.alerts_list = []

    def setup_tabs(self):
        """Настройка вкладок"""
        self.tabview = ctk.CTkTabview(self, fg_color="#2d2d2d")  # Темный фон для вкладок
        self.tabview.pack(fill=ctk.BOTH, expand=True, padx=10)
        
        # Вкладка текущего состояния
        self.current_tab = self.tabview.add("Текущее состояние")
        self.current_status_tab = CurrentStatusTab(self.current_tab, self.monitor, self.db, self.alert_manager)
        
        # Вкладка исторических графиков
        self.graphs_tab = self.tabview.add("История метрик")
        self.history_graphs_tab = HistoryGraphsTab(self.graphs_tab, self.monitor, self.db)
        
        # Вкладка инцидентов
        self.incidents_tab = self.tabview.add("История инцидентов")
        self.incidents_tab_instance = IncidentsTab(self.incidents_tab, self.db)
        
        # Настраиваем фрейм оповещений под Tabview
        self.setup_alerts_frame()
        
        # Загружаем графики за последний час для выбранного сервера при запуске
        self.history_graphs_tab.update_graphs()
        
        # Запускаем первое обновление данных и планируем периодические обновления
        self.get_all_data()
        self.update_all_data()
        self.after(5000, self.update_data_periodically)

    def show_connection(self):
        """Отображение панели подключения"""
        self.connectionLabel = ctk.CTkLabel(self.connectionFrame, text="Сервер: ", justify="left", 
                                          font=("Arial", 16), text_color="#ffffff")
        self.connectionLabel.grid(row=0, column=0, padx=10)

        self.connectionEntry = ctk.CTkOptionMenu(self.connectionFrame, values=self.servers, 
                                               command=lambda _: self.change_server(),
                                               fg_color="#3d3d3d", button_color="#4d4d4d")
        self.connectionEntry.grid(row=0, column=1, padx=10)

        self.connectionButton = ctk.CTkButton(self.connectionFrame, text='Серверы', 
                                            command=self.open_servers_window,
                                            fg_color="#4d4d4d", hover_color="#5d5d5d")
        self.connectionButton.grid(row=0, column=2, padx=10)

        self.connectionStatusLabel = ctk.CTkLabel(self.connectionFrame, text="Подключение отсутствует", 
                                                justify="left", font=("Arial", 16), text_color="#FF6D6A")
        self.connectionStatusLabel.grid(row=0, column=3, padx=10)

    def update_connection_info(self):
        """Обновление информации о подключении"""
        try:
            if self.connection_info:
                if self.connection_info == "1":
                    connection_text = "Подключено"
                    self.connectionStatusLabel.configure(text=connection_text, text_color="#a8e4a0")
                    return True
                else:
                    connection_text = "Подключение отсутствует"
                    self.connectionStatusLabel.configure(text=connection_text, text_color="#FF6D6A")
                    return False
            else:
                connection_text = "Подключение отсутствует"
                self.connectionStatusLabel.configure(text=connection_text, text_color="#FF6D6A")
                return False
        except Exception as e:
            connection_text = "Подключение отсутствует"
            self.connectionStatusLabel.configure(text=connection_text, text_color="#FF6D6A")
            return False

    def update_data_periodically(self):
        """Периодическое обновление данных"""
        threading.Thread(target=self.get_all_data, daemon=True).start()
        self.update_all_data()
        # Планируем следующее обновление через 5 секунд
        self.after(5000, self.update_data_periodically)

    def get_all_data(self):
        """Получение всех данных"""
        try:
            self.connection_info = self.monitor.is_network_available() if self.monitor else "0"
            self.cpu_info = self.monitor.get_cpu_info() if self.monitor else None
            self.ram_info = self.monitor.get_RAM_info() if self.monitor else None
            self.rom_info = self.monitor.get_ROM_info() if self.monitor else None
            
            # Сохраняем метрики в базу данных
            if self.cpu_info and self.ram_info and self.rom_info:
                cpu_usage = float(self.cpu_info.get('usage_precent', 0))
                ram_usage = float(self.ram_info.get('usage_precent', 0))
                temperature = float(self.cpu_info.get('temperatur', 0))
                
                self.db.save_metrics(self.selected_url, cpu_usage, ram_usage, temperature, self.rom_info)
                
                # Проверяем оповещения
                self.alert_manager.check_alerts(self.selected_url, self.cpu_info, self.ram_info, self.rom_info)
                
        except Exception as e:
            # Логируем ошибку, но не прерываем работу приложения
            print(f"Ошибка при получении данных: {e}")
            self.connection_info = "0"
            self.cpu_info = None
            self.ram_info = None
            self.rom_info = None

    def update_all_data(self):
        """Обновление всех данных в интерфейсе"""
        try:
            connected = self.update_connection_info()
            if connected:
                self.current_status_tab.update_all_data(self.cpu_info, self.ram_info, self.rom_info)
                self.show_alerts()  # Обновляем оповещения
            else:
                self.current_status_tab.reset_data()
                self.show_alerts()  # Обновляем оповещения даже при отсутствии подключения
        except Exception as e:
            pass

    def change_server(self):
        """Смена сервера"""
        self.selected_url = self.connectionEntry.get()
        try:
            if self.monitor:
                self.monitor.change_url(self.selected_url)
            else:
                self.monitor = PrometheusMonitor(self.selected_url)
            self.reset_all_data()
            # Не сбрасываем период, просто обновляем графики для текущего выбранного периода
            self.history_graphs_tab.update_graphs()
        except Exception as e:
            print(f"Ошибка при смене сервера: {e}")
            self.monitor = None

    def reset_all_data(self):
        """Сброс всех данных"""
        self.connection_info = []
        self.cpu_info = []
        self.ram_info = []
        self.rom_info = []
        self.connectionStatusLabel.configure(text="Подключение отсутствует", text_color="#FF6D6A")
        self.current_status_tab.reset_data()

    def open_servers_window(self):
        """Открытие окна управления серверами"""
        servers_window = ctk.CTkToplevel(self)
        servers_window.title("Добавление сервера")
        ServersWindow(servers_window, self, self.db)

    def update_servers(self):
        """Обновление списка серверов"""
        self.servers = self.db.servers
        self.connectionEntry.configure(values=self.servers)

    def show_alerts(self):
        """Отображает активные оповещения"""
        # Очищаем старые оповещения
        for alert_widget in self.alerts_list:
            alert_widget.destroy()
        self.alerts_list.clear()

        # Получаем активные оповещения
        alerts = self.alert_manager.get_active_alerts()
        
        if not alerts:
            no_alerts_label = ctk.CTkLabel(self.alerts_container, text="Нет активных оповещений", 
                                          text_color="#a8e4a0", font=("Arial", 14))
            no_alerts_label.pack(anchor='w', padx=10, pady=5)
            self.alerts_list.append(no_alerts_label)
            return

        for alert in alerts:
            alert_frame = ctk.CTkFrame(self.alerts_container)
            alert_frame.pack(fill=ctk.X, padx=5, pady=2)
            
            # Определяем цвет в зависимости от типа оповещения
            if "КРИТИЧЕСКОЕ" in alert[4]:  # message
                color = "#FF6D6A"
            else:
                color = "#FFA500"
            
            # Форматируем время
            timestamp_str = alert[2]  # timestamp
            try:
                if timestamp_str:
                    # Парсим SQLite timestamp
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
                print(f"Ошибка парсинга времени оповещения '{timestamp_str}': {e}")
                time_display = str(timestamp_str) if timestamp_str else "Н/Д"
            
            alert_text = f"{alert[4]} - {time_display}"  # message - formatted timestamp
            alert_label = ctk.CTkLabel(alert_frame, text=alert_text, text_color=color, 
                                      font=("Arial", 12), wraplength=800)
            alert_label.pack(side=ctk.LEFT, padx=10, pady=5)
            
            ack_button = ctk.CTkButton(alert_frame, text="✓", width=30, 
                                      command=lambda aid=alert[0]: self.acknowledge_alert(aid))
            ack_button.pack(side=ctk.RIGHT, padx=5, pady=5)
            
            self.alerts_list.append(alert_frame)

    def acknowledge_alert(self, alert_id):
        """Подтверждает оповещение"""
        self.alert_manager.acknowledge_alert(alert_id)
        self.show_alerts()