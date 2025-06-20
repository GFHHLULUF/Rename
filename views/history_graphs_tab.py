import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import json
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MultipleLocator

class HistoryGraphsTab:
    def __init__(self, parent, monitor, database):
        self.parent = parent
        self.monitor = monitor
        self.db = database
        
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса"""
        # Верхняя панель с выпадающим списком выбора периода и кнопкой обновления
        self.control_frame = ctk.CTkFrame(self.parent)
        self.control_frame.pack(fill=ctk.X, padx=10, pady=5)
        
        self.period_label = ctk.CTkLabel(self.control_frame, text="Период:", font=("Arial", 14))
        self.period_label.pack(side=ctk.LEFT, padx=10, pady=5)
        
        # Выпадающий список для выбора периода
        self.period_options = [
            ("1 час", 1),
            ("24 часа", 24),
            ("48 часов", 48),
            ("168 часов", 168)
        ]
        
        self.period_values = [option[1] for option in self.period_options]
        self.period_names = [option[0] for option in self.period_options]
        
        self.period_dropdown = ctk.CTkOptionMenu(
            self.control_frame,
            values=self.period_names,
            command=self.change_period,
            width=150
        )
        self.period_dropdown.pack(side=ctk.LEFT, padx=10, pady=5)
        self.period_dropdown.set("1 час")  # По умолчанию 1 час
        
        # Кнопка обновления графиков
        self.refresh_button = ctk.CTkButton(
            self.control_frame,
            text="Обновить графики",
            command=self.refresh_graphs,
            width=150
        )
        self.refresh_button.pack(side=ctk.RIGHT, padx=10, pady=5)
        
        # Основной контейнер для графиков
        self.main_container = ctk.CTkScrollableFrame(self.parent)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        
        # Создаем графики
        self.setup_graphs()

        # Теперь можно синхронизировать период и график
        self.period_dropdown.set("1 час")
        self.change_period("1 час")

    def setup_graphs(self):
        """Создание графиков"""
        # График CPU
        self.cpu_frame = ctk.CTkFrame(self.main_container)
        self.cpu_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        self.cpu_label = ctk.CTkLabel(self.cpu_frame, text="История использования CPU", 
                                     font=("Arial", 16, "bold"))
        self.cpu_label.pack(anchor='w', padx=10, pady=5)
        
        self.cpu_canvas_frame = ctk.CTkFrame(self.cpu_frame, fg_color="#2b2b2b")  # Темный фон
        self.cpu_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        
        # График RAM
        self.ram_frame = ctk.CTkFrame(self.main_container)
        self.ram_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        self.ram_label = ctk.CTkLabel(self.ram_frame, text="История использования RAM", 
                                     font=("Arial", 16, "bold"))
        self.ram_label.pack(anchor='w', padx=10, pady=5)
        
        self.ram_canvas_frame = ctk.CTkFrame(self.ram_frame, fg_color="#2b2b2b")  # Темный фон
        self.ram_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        
        # График температуры
        self.temp_frame = ctk.CTkFrame(self.main_container)
        self.temp_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        self.temp_label = ctk.CTkLabel(self.temp_frame, text="История температуры CPU", 
                                      font=("Arial", 16, "bold"))
        self.temp_label.pack(anchor='w', padx=10, pady=5)
        
        self.temp_canvas_frame = ctk.CTkFrame(self.temp_frame, fg_color="#2b2b2b")  # Темный фон
        self.temp_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        
        # График дисков
        self.disks_frame = ctk.CTkFrame(self.main_container)
        self.disks_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        self.disks_label = ctk.CTkLabel(self.disks_frame, text="История использования дисков", 
                                       font=("Arial", 16, "bold"))
        self.disks_label.pack(anchor='w', padx=10, pady=5)
        
        self.disks_canvas_frame = ctk.CTkFrame(self.disks_frame, fg_color="#2b2b2b")  # Темный фон
        self.disks_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)

    def parse_sqlite_timestamp(self, timestamp_str):
        """Парсинг временной метки из SQLite в datetime объект"""
        if not timestamp_str:
            return None
            
        try:
            # Пробуем разные форматы времени
            formats = [
                '%Y-%m-%d %H:%M:%S',  # Стандартный SQLite формат
                '%Y-%m-%d %H:%M:%S.%f',  # С микросекундами
                '%Y-%m-%dT%H:%M:%S',  # ISO формат без Z
                '%Y-%m-%dT%H:%M:%S.%f',  # ISO формат с микросекундами
                '%Y-%m-%dT%H:%M:%SZ',  # ISO формат с Z
                '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO формат с микросекундами и Z
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.datetime.strptime(timestamp_str, fmt)
                    return dt
                except ValueError:
                    continue
            
            # Если ни один формат не подошел, выводим отладочную информацию
            print(f"Не удалось распарсить timestamp: {timestamp_str}")
            return None
            
        except Exception as e:
            print(f"Ошибка при парсинге timestamp '{timestamp_str}': {e}")
            return None

    def format_time_axis(self, ax):
        """Форматирование оси времени для графиков"""
        import matplotlib.dates as mdates
        from matplotlib.ticker import FuncFormatter
        
        # Настраиваем форматирование времени - одинаковый формат для всех периодов
        def time_formatter(x, pos):
            try:
                dt = mdates.num2date(x)
                return dt.strftime('%d.%m %H:%M')
            except:
                return ''
        
        period = self.period_values[self.period_names.index(self.period_dropdown.get())]
        if period == 1:
            locator = mdates.MinuteLocator(interval=5)
        elif period == 24:
            locator = mdates.MinuteLocator(interval=15)
        elif period == 48:
            locator = mdates.HourLocator(interval=2)  # Каждые 2 часа
        elif period == 168:
            locator = mdates.HourLocator(interval=6)  # Каждые 6 часов
        elif period > 168:
            locator = mdates.DayLocator()
        else:
            locator = mdates.MinuteLocator(interval=15)
        
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(FuncFormatter(time_formatter))
        
        # Настройка внешнего вида - уменьшенный размер шрифта для времени
        ax.tick_params(colors='white', labelsize=7)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    def format_value_axis(self, ax, ylabel_text):
        """Форматирование оси значений для лучшей читаемости"""
        from matplotlib.ticker import FuncFormatter, MultipleLocator
        
        # Форматирование значений оси Y
        def value_formatter(x, pos):
            if ylabel_text == 'Температура (°C)':
                return f'{x:.0f}°C'
            else:
                return f'{x:.0f}%'
        
        # Настраиваем интервалы для оси Y
        if ylabel_text == 'Температура (°C)':
            # Для температуры: от 0 до 100°C с интервалом 10°C
            ax.set_ylim(0, 100)
            ax.yaxis.set_major_locator(MultipleLocator(10))
        else:
            # Для процентов: от 0 до 100% с интервалом 10%
            ax.set_ylim(0, 100)
            ax.yaxis.set_major_locator(MultipleLocator(10))
        
        ax.yaxis.set_major_formatter(FuncFormatter(value_formatter))
        
        # Настройка внешнего вида оси Y
        ax.tick_params(axis='y', colors='white', labelsize=12)
        ax.set_ylabel(ylabel_text, fontsize=14, color='white', fontweight='bold')
        
        # Улучшаем читаемость сетки
        ax.grid(True, linestyle='--', alpha=0.3, color='#ffffff')
        ax.grid(True, axis='y', linestyle='-', alpha=0.2, color='#ffffff')

    def setup_graph_style(self, ax, title_text):
        """Настройка общего стиля графика"""
        # Заголовок
        ax.set_title(title_text, fontsize=16, color='white', fontweight='bold', pad=20)
        
        # Убираем подпись оси X (Время)
        # ax.set_xlabel('Время', fontsize=14, color='white', fontweight='bold')
        
        # Настройка внешнего вида - только для оси Y, время настраивается отдельно
        ax.tick_params(axis='y', colors='white', labelsize=11)
        
        # Убираем рамку
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#666666')
        ax.spines['left'].set_color('#666666')
        
        # Настройка легенды
        if ax.get_legend():
            legend = ax.get_legend()
            legend.get_frame().set_facecolor('#2b2b2b')
            legend.get_frame().set_alpha(0.9)
            for text in legend.get_texts():
                text.set_color('white')
                text.set_fontsize(11)

    def change_period(self, period_name):
        """Изменение периода отображения"""
        self.period_dropdown.set(period_name)
        self.update_graphs()

    def update_graphs(self):
        """Обновление всех графиков"""
        self.update_cpu_graph()
        self.update_ram_graph()
        self.update_temperature_graph()
        self.update_disks_graph()

    def update_cpu_graph(self):
        """Обновление графика CPU"""
        # Очищаем старый график
        for widget in self.cpu_canvas_frame.winfo_children():
            widget.destroy()
        
        # Принудительно устанавливаем темный фон
        self.cpu_canvas_frame.configure(fg_color="#2b2b2b")
        
        # Мгновенно добавляем невидимый плейсхолдер
        placeholder = ctk.CTkLabel(self.cpu_canvas_frame, text="", fg_color="#2b2b2b")
        placeholder.pack(fill="both", expand=True)
        
        # Принудительно обновляем интерфейс
        self.cpu_canvas_frame.update()
        
        # Получаем данные
        data = self.db.get_metrics_history(self.monitor.prom.url, self.period_values[self.period_names.index(self.period_dropdown.get())])
        
        # Удаляем плейсхолдер
        placeholder.destroy()
        
        if not data:
            no_data_label = ctk.CTkLabel(self.cpu_canvas_frame, text="Нет данных за выбранный период", 
                                        font=("Arial", 16), text_color="#ffffff")
            no_data_label.pack(expand=True)
            return
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        timestamps = []
        cpu_values = []
        
        for row in data:
            timestamp_str = row[0]  # timestamp
            cpu_usage = row[1] if row[1] is not None else 0  # cpu_usage
            
            # Парсим timestamp из SQLite
            dt = self.parse_sqlite_timestamp(timestamp_str)
            if dt:
                timestamps.append(dt)
                cpu_values.append(float(cpu_usage))
        
        if timestamps:
            ax.plot(timestamps, cpu_values, color='#aec7e8', linewidth=2, marker='o', markersize=3)
            
            # Настройка стиля графика
            self.setup_graph_style(ax, f'Использование CPU за {self.period_values[self.period_names.index(self.period_dropdown.get())]} часов')
            
            # Форматирование осей
            self.format_time_axis(ax)
            self.format_value_axis(ax, 'Использование CPU (%)')
            
            canvas = FigureCanvasTkAgg(fig, master=self.cpu_canvas_frame)
            canvas.get_tk_widget().pack(fill='both', expand=True)
            canvas.draw()

    def update_ram_graph(self):
        """Обновление графика RAM"""
        # Очищаем старый график
        for widget in self.ram_canvas_frame.winfo_children():
            widget.destroy()
        
        # Принудительно устанавливаем темный фон
        self.ram_canvas_frame.configure(fg_color="#2b2b2b")
        
        # Принудительно обновляем интерфейс
        self.ram_canvas_frame.update()
        
        # Получаем данные
        data = self.db.get_metrics_history(self.monitor.prom.url, self.period_values[self.period_names.index(self.period_dropdown.get())])
        
        if not data:
            no_data_label = ctk.CTkLabel(self.ram_canvas_frame, text="Нет данных за выбранный период", 
                                        font=("Arial", 16), text_color="#ffffff")
            no_data_label.pack(expand=True)
            return
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        timestamps = []
        ram_values = []
        
        for row in data:
            timestamp_str = row[0]  # timestamp
            ram_usage = row[2] if row[2] is not None else 0  # ram_usage
            
            # Парсим timestamp из SQLite
            dt = self.parse_sqlite_timestamp(timestamp_str)
            if dt:
                timestamps.append(dt)
                ram_values.append(float(ram_usage))
        
        if timestamps:
            ax.plot(timestamps, ram_values, color='#98df8a', linewidth=2, marker='o', markersize=3)
            
            # Настройка стиля графика
            self.setup_graph_style(ax, f'Использование RAM за {self.period_values[self.period_names.index(self.period_dropdown.get())]} часов')
            
            # Форматирование осей
            self.format_time_axis(ax)
            self.format_value_axis(ax, 'Использование RAM (%)')
            
            canvas = FigureCanvasTkAgg(fig, master=self.ram_canvas_frame)
            canvas.get_tk_widget().pack(fill='both', expand=True)
            canvas.draw()

    def update_temperature_graph(self):
        """Обновление графика температуры"""
        # Очищаем старый график
        for widget in self.temp_canvas_frame.winfo_children():
            widget.destroy()
        
        # Принудительно устанавливаем темный фон
        self.temp_canvas_frame.configure(fg_color="#2b2b2b")
        
        # Принудительно обновляем интерфейс
        self.temp_canvas_frame.update()
        
        # Получаем данные
        data = self.db.get_metrics_history(self.monitor.prom.url, self.period_values[self.period_names.index(self.period_dropdown.get())])
        
        if not data:
            no_data_label = ctk.CTkLabel(self.temp_canvas_frame, text="Нет данных за выбранный период", 
                                        font=("Arial", 16), text_color="#ffffff")
            no_data_label.pack(expand=True)
            return
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        timestamps = []
        temp_values = []
        
        for row in data:
            timestamp_str = row[0]  # timestamp
            temperature = row[3] if row[3] is not None else 0  # temperature
            
            # Парсим timestamp из SQLite
            dt = self.parse_sqlite_timestamp(timestamp_str)
            if dt:
                timestamps.append(dt)
                temp_values.append(float(temperature))
        
        if timestamps:
            ax.plot(timestamps, temp_values, color='#ff9896', linewidth=2, marker='o', markersize=3)
            
            # Настройка стиля графика
            self.setup_graph_style(ax, f'Температура CPU за {self.period_values[self.period_names.index(self.period_dropdown.get())]} часов')
            
            # Добавляем линию критической температуры
            ax.axhline(y=85, color='red', linestyle='--', alpha=0.7, label='Критическая температура (85°C)')
            
            # Форматирование осей
            self.format_time_axis(ax)
            self.format_value_axis(ax, 'Температура (°C)')
            
            # Настройка легенды
            legend = ax.legend()
            legend.get_frame().set_facecolor('#2b2b2b')
            legend.get_frame().set_alpha(0.9)
            for text in legend.get_texts():
                text.set_color('white')
                text.set_fontsize(11)
            
            canvas = FigureCanvasTkAgg(fig, master=self.temp_canvas_frame)
            canvas.get_tk_widget().pack(fill='both', expand=True)
            canvas.draw()

    def update_disks_graph(self):
        """Обновление графика дисков"""
        # Очищаем старый график
        for widget in self.disks_canvas_frame.winfo_children():
            widget.destroy()
        
        # Принудительно устанавливаем темный фон
        self.disks_canvas_frame.configure(fg_color="#2b2b2b")
        
        # Принудительно обновляем интерфейс
        self.disks_canvas_frame.update()
        
        # Получаем данные
        data = self.db.get_metrics_history(self.monitor.prom.url, self.period_values[self.period_names.index(self.period_dropdown.get())])
        
        if not data:
            no_data_label = ctk.CTkLabel(self.disks_canvas_frame, text="Нет данных за выбранный период", 
                                        font=("Arial", 16), text_color="#ffffff")
            no_data_label.pack(expand=True)
            return
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        # Собираем данные по дискам
        disk_data = {}
        
        for row in data:
            timestamp_str = row[0]  # timestamp
            disk_usage_json = row[4]  # disk_usage
            
            if disk_usage_json:
                # Парсим timestamp из SQLite
                dt = self.parse_sqlite_timestamp(timestamp_str)
                if dt:
                    try:
                        disk_info = json.loads(disk_usage_json)
                        
                        for volume, usage in disk_info.items():
                            if volume not in disk_data:
                                disk_data[volume] = {'timestamps': [], 'usage': []}
                            
                            disk_data[volume]['timestamps'].append(dt)
                            disk_data[volume]['usage'].append(float(usage['usage_precent']))
                    except:
                        continue
        
        if disk_data:
            colors = ['#aec7e8', '#98df8a', '#ff9896', '#c5b0d5', '#ffbb78', '#2ca02c']
            color_idx = 0
            
            for volume, data_points in disk_data.items():
                if data_points['timestamps']:
                    color = colors[color_idx % len(colors)]
                    ax.plot(data_points['timestamps'], data_points['usage'], 
                           color=color, linewidth=2, marker='o', markersize=3, 
                           label=f'Диск {volume}')
                    color_idx += 1
            
            # Настройка стиля графика
            self.setup_graph_style(ax, f'Использование дисков за {self.period_values[self.period_names.index(self.period_dropdown.get())]} часов')
            
            # Добавляем линию критического использования
            ax.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='Критическое использование (90%)')
            
            # Форматирование осей
            self.format_time_axis(ax)
            self.format_value_axis(ax, 'Использование (%)')
            
            # Настройка легенды
            legend = ax.legend()
            legend.get_frame().set_facecolor('#2b2b2b')
            legend.get_frame().set_alpha(0.9)
            for text in legend.get_texts():
                text.set_color('white')
                text.set_fontsize(11)
            
            canvas = FigureCanvasTkAgg(fig, master=self.disks_canvas_frame)
            canvas.get_tk_widget().pack(fill='both', expand=True)
            canvas.draw()
        else:
            no_data_label = ctk.CTkLabel(self.disks_canvas_frame, text="Нет данных о дисках за выбранный период", 
                                        font=("Arial", 16), text_color="#ffffff")
            no_data_label.pack(expand=True)

    def refresh_graphs(self):
        """Обновление всех графиков"""
        # Обновляем графики последовательно с большой задержкой
        self.parent.after(500, self.update_cpu_graph)
        self.parent.after(600, self.update_ram_graph)
        self.parent.after(700, self.update_temperature_graph)
        self.parent.after(800, self.update_disks_graph) 