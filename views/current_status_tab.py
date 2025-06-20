import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

class CurrentStatusTab:
    def __init__(self, parent, monitor, database, alert_manager):
        self.parent = parent
        self.monitor = monitor
        self.db = database
        self.alert_manager = alert_manager
        
        self.setup_ui()
        self.initialize_data()

    def setup_ui(self):
        """Настройка интерфейса"""
        self.mainframe = ctk.CTkScrollableFrame(self.parent)
        self.mainframe.pack(fill=ctk.BOTH, expand=True)

        # Фрейм для CPU
        self.cpuFrame = ctk.CTkFrame(self.mainframe)
        self.cpuFrame.pack(fill=ctk.X, padx=5, pady=5)

        # Фрейм для RAM
        self.ramFrame = ctk.CTkFrame(self.mainframe)
        self.ramFrame.pack(fill=ctk.X, padx=5, pady=10)

        # Фрейм для дисков
        self.bottom_frame = ctk.CTkFrame(self.mainframe)
        self.bottom_frame.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)

        self.show_cpu_info()
        self.show_ram_info()
        self.show_rom_info()

    def show_cpu_info(self):
        """Отображение информации о процессоре"""
        self.cpuInfoFrame = ctk.CTkFrame(self.cpuFrame, width=400)
        self.cpuInfoFrame.pack(side=ctk.LEFT, fill=ctk.Y)
        self.cpuInfoFrame.pack_propagate(False)

        self.cpuLabel = ctk.CTkLabel(self.cpuInfoFrame, text="Информация о процессоре:", 
                                    justify="left", font=("Arial", 18))
        self.cpuLabel.pack(anchor='nw', padx=10, pady=10)

        self.cpuInfoLabel = ctk.CTkLabel(self.cpuInfoFrame, text="Нет данных", 
                                        justify="left", font=("Arial", 14))
        self.cpuInfoLabel.pack(anchor='w', padx=10, pady=5)

        self.cpuGraphicFrame = ctk.CTkFrame(self.cpuFrame, corner_radius=10)
        self.cpuGraphicFrame.pack(fill=ctk.X)

        plt.style.use('dark_background') 
        self.fig, self.ax_cpu = plt.subplots(figsize=(10, 5), dpi=100)
        self.fig.patch.set_facecolor('#3a3a3a') 
        self.ax_cpu.set_facecolor('#3a3a3a')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.cpuGraphicFrame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.ax_cpu.set_title('Процент использования процессора', fontsize=18, pad=20, color='white')
        self.ax_cpu.set_xlabel('Время', fontsize=16, color='white')
        self.ax_cpu.set_ylabel('Загрузка CPU (%)', fontsize=16, color='white')
        self.ax_cpu.grid(True, linestyle='--', alpha=0.6, color='#ffffff')
        self.ax_cpu.set_ylim(0, 100)

        self.data_cpu = []
        self.timestamps = []

    def show_ram_info(self):
        """Отображение информации об ОЗУ"""
        self.ramInfoFrame = ctk.CTkFrame(self.ramFrame, width=400)
        self.ramInfoFrame.pack(side=ctk.LEFT, fill=ctk.Y)
        self.ramInfoFrame.pack_propagate(False)

        self.ramLabel = ctk.CTkLabel(self.ramInfoFrame, text="Информация об ОЗУ:", 
                                    justify="left", font=("Arial", 18))
        self.ramLabel.pack(anchor='nw', padx=10, pady=10)

        self.ramInfoLabel = ctk.CTkLabel(self.ramInfoFrame, text="Нет данных", 
                                        justify="left", font=("Arial", 14))
        self.ramInfoLabel.pack(anchor='nw', padx=10, pady=5)

        self.ramGraphicFrame = ctk.CTkFrame(self.ramFrame, corner_radius=10)
        self.ramGraphicFrame.pack(fill=ctk.X)

        plt.style.use('dark_background')
        self.fig_ram, self.ax_ram = plt.subplots(figsize=(10, 5), dpi=100)
        self.fig_ram.patch.set_facecolor('#3a3a3a')
        self.ax_ram.set_facecolor('#3a3a3a')

        self.canvas_ram = FigureCanvasTkAgg(self.fig_ram, master=self.ramGraphicFrame)
        self.canvas_ram.get_tk_widget().pack(fill='both', expand=True)

        self.ax_ram.set_title('Процент использования ОЗУ', fontsize=18, pad=20, color='white')
        self.ax_ram.set_xlabel('Время', fontsize=16, color='white')
        self.ax_ram.set_ylabel('Загрузка RAM (%)', fontsize=16, color='white')
        self.ax_ram.grid(True, linestyle='--', alpha=0.6, color='#ffffff')
        self.ax_ram.set_ylim(0, 100)

        self.data_ram_usage = []
        self.timestamps_ram = []

    def show_rom_info(self):
        """Отображение информации о дисках"""
        self.romScrollFrame = ctk.CTkFrame(self.bottom_frame)
        self.romScrollFrame.pack(fill=ctk.BOTH, expand=True)

        self.rom_label = ctk.CTkLabel(self.romScrollFrame, text="Информация о дисках", 
                                     font=("Arial", 18))
        self.rom_label.pack(anchor='w', padx=10, pady=5)

        self.rom_disks_container = ctk.CTkFrame(self.romScrollFrame)
        self.rom_disks_container.pack(fill='x', expand=True, padx=5, pady=5)
        self.rom_disks_container.grid_columnconfigure(0, weight=1)
        self.rom_disks_container.grid_columnconfigure(1, weight=1)
        self.rom_disks = {}

    def initialize_data(self):
        """Инициализация данных"""
        self.cpu_info = None
        self.ram_info = None
        self.rom_info = None

    def update_cpu_info(self):
        """Обновление информации о процессоре"""
        if self.cpu_info:
            cpu_text = (
                f"Название: {self.cpu_info['name']}\n"
                f"Описание: {self.cpu_info['description']}\n"
                f"Частота: {self.cpu_info['frequency_mhz']} МГц\n"
                f"Количество ядер: {self.cpu_info['core']}\n"
                f"Потоков: {self.cpu_info['thread']}\n"
                f"L2 кэш: {self.cpu_info['L2']} KB\n"
                f"L3 кэш: {self.cpu_info['L3']} KB\n"
                f"Использование: {self.cpu_info['usage_precent']:.2f}%\n"
                f"Температура: {float(self.cpu_info['temperatur']):.2f}°C"
            )
            self.cpuInfoLabel.configure(text=cpu_text, wraplength=300)

            cpu_usage = float(self.cpu_info['usage_precent'])
            if len(self.data_cpu) > 10:
                self.data_cpu.pop(0)
                self.timestamps.pop(0)
            self.data_cpu.append(cpu_usage)
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.timestamps.append(now)

            self.ax_cpu.clear()
            self.ax_cpu.plot(
                self.timestamps, self.data_cpu,
                label="CPU %",
                color="#aec7e8",
                marker='o',
                markersize=4
            )
            self.ax_cpu.set_title('Процент использования процессора', fontsize=18, pad=20, color='white')
            self.ax_cpu.set_xlabel('Время', fontsize=16, color='white')
            self.ax_cpu.set_ylabel('Загрузка CPU (%)', fontsize=16, color='white')
            self.ax_cpu.grid(True, linestyle='--', alpha=0.6, color='#ffffff')
            self.ax_cpu.legend()
            self.ax_cpu.set_ylim(0, 100)
            self.canvas.draw()

    def update_ram_info(self):
        """Обновление информации об ОЗУ"""
        if self.ram_info:
            ram_text = (
                f"Использование: {float(self.ram_info['usage_precent']):.2f}%\n"
                f"Свободно: {float(self.ram_info['available']):.2f} ГБ\n"
                f"Используется: {float(self.ram_info['use']):.2f} ГБ\n"
                f"Всего: {float(self.ram_info['all']):.2f} ГБ"
            )
            self.ramInfoLabel.configure(text=ram_text, wraplength=400)

            ram_usage = float(self.ram_info['usage_precent'])
            if len(self.data_ram_usage) > 10:
                self.data_ram_usage.pop(0)
                self.timestamps_ram.pop(0)
            self.data_ram_usage.append(ram_usage)
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.timestamps_ram.append(now)

            self.ax_ram.clear()
            self.ax_ram.plot(
                self.timestamps_ram, self.data_ram_usage,
                label="RAM %",
                color="#98df8a", 
                marker='o',
                markersize=4
            )
            self.ax_ram.set_title('Процент использования ОЗУ', fontsize=18, pad=20, color='white')
            self.ax_ram.set_xlabel('Время', fontsize=16, color='white')
            self.ax_ram.set_ylabel('Загрузка RAM (%)', fontsize=16, color='white')
            self.ax_ram.grid(True, linestyle='--', alpha=0.6, color='#ffffff')
            self.ax_ram.legend()
            self.ax_ram.set_ylim(0, 100)
            self.canvas_ram.draw()

    def update_rom_info(self):
        """Обновление информации о дисках"""
        if not self.rom_info:
            return

        volumes = list(self.rom_info.keys())
        current_volumes = set(self.rom_disks.keys())
        new_volumes = set(self.rom_info.keys())

        for volume in current_volumes - new_volumes:
            self.rom_disks[volume]['frame'].destroy()
            del self.rom_disks[volume]

        for idx, volume in enumerate(volumes):
            disk_data = self.rom_info[volume]
            use = float(disk_data['use'])
            free = float(disk_data['available'])
            total = float(disk_data['all'])
            usage_percent = float(disk_data['usage_precent'])

            if volume not in self.rom_disks:
                frame = ctk.CTkFrame(self.rom_disks_container)
                frame.grid(row=idx//2, column=idx%2, padx=10, pady=10, sticky="nsew")
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_rowconfigure(1, weight=1)

                label_title = ctk.CTkLabel(frame, text=f"Диск: {volume}", font=("Arial", 16))
                label_title.grid(row=0, column=0, sticky='w', padx=10, pady=5)

                info_text = (
                    f"Всего: {total:.2f} ГБ\n"
                    f"Используется: {use:.2f} ГБ\n"
                    f"Свободно: {free:.2f} ГБ\n"
                    f"Использовано: {usage_percent:.1f}%"
                )
                label_info = ctk.CTkLabel(frame, text=info_text, justify="left", font=("Arial", 14))
                label_info.grid(row=1, column=0, sticky='nw', padx=10, pady=5)

                fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
                fig.patch.set_facecolor('#2b2b2b')
                ax.set_facecolor('#2b2b2b')

                canvas_frame = ctk.CTkFrame(frame)
                canvas_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
                canvas_frame.grid_columnconfigure(0, weight=1)
                canvas_frame.grid_rowconfigure(0, weight=1)

                canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
                canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

                self.rom_disks[volume] = {
                    'frame': frame,
                    'fig': fig,
                    'ax': ax,
                    'canvas': canvas,
                    'label_info': label_info
                }
            else:
                frame = self.rom_disks[volume]['frame']
                frame.grid(row=idx//2, column=idx%2, padx=10, pady=10, sticky="nsew")
                info_text = (
                    f"Всего: {total:.2f} ГБ\n"
                    f"Используется: {use:.2f} ГБ\n"
                    f"Свободно: {free:.2f} ГБ\n"
                    f"Использовано: {usage_percent:.1f}%"
                )
                self.rom_disks[volume]['label_info'].configure(text=info_text)

            disk_plot = self.rom_disks[volume]
            ax = disk_plot['ax']
            ax.clear()

            bar_width = 0.4
            x_indexes = [1]
            ax.bar([x - bar_width / 2 for x in x_indexes], [use], width=bar_width,
                label='Использовано (ГБ)', color='#FF6D6A')
            ax.bar([x + bar_width / 2 for x in x_indexes], [free], width=bar_width,
                label='Свободно (ГБ)', color='#a8e4a0')  

            ax.set_title(f'{volume}', fontsize=18, color='white')
            ax.set_xticks([])
            ax.set_ylabel('Объем (ГБ)', fontsize=16, color='white')
            ax.grid(True, axis='y', linestyle='--', alpha=0.6, color='#ffffff')
            ax.legend()

            for bars in ax.containers:
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                color='white')

            disk_plot['canvas'].draw()

    def update_all_data(self, cpu_info, ram_info, rom_info):
        """Обновление всех данных"""
        self.cpu_info = cpu_info
        self.ram_info = ram_info
        self.rom_info = rom_info
        
        if cpu_info and ram_info and rom_info:
            self.update_cpu_info()
            self.update_ram_info()
            self.update_rom_info()

    def reset_data(self):
        """Сброс всех данных"""
        self.cpu_info = None
        self.ram_info = None
        self.rom_info = None
        
        self.cpuInfoLabel.configure(text="Нет данных")
        self.ramInfoLabel.configure(text="Нет данных")
        
        # Очищаем графики
        self.data_cpu.clear()
        self.timestamps.clear()
        self.ax_cpu.clear()
        self.ax_cpu.set_title('Процент использования процессора', fontsize=18, pad=20, color='white')
        self.ax_cpu.set_xlabel('Время', fontsize=16, color='white')
        self.ax_cpu.set_ylabel('Загрузка CPU (%)', fontsize=16, color='white')
        self.ax_cpu.grid(True, linestyle='--', alpha=0.6, color='#ffffff')
        self.ax_cpu.set_ylim(0, 100)
        self.canvas.draw()

        self.data_ram_usage.clear()
        self.timestamps_ram.clear()
        self.ax_ram.clear()
        self.ax_ram.set_title('Процент использования ОЗУ', fontsize=18, pad=20, color='white')
        self.ax_ram.set_xlabel('Время', fontsize=16, color='white')
        self.ax_ram.set_ylabel('Загрузка RAM (%)', fontsize=16, color='white')
        self.ax_ram.grid(True, linestyle='--', alpha=0.6, color='#ffffff')
        self.ax_ram.set_ylim(0, 100)
        self.canvas_ram.draw()

        # Очищаем диски
        for volume in list(self.rom_disks.keys()):
            self.rom_disks[volume]['frame'].destroy()
        self.rom_disks = {} 