from views.app import App
import customtkinter as ctk
import traceback
import matplotlib.pyplot as plt

if __name__ == "__main__":
    try:
        # Настройка темы приложения
        ctk.set_appearance_mode("dark")  # Устанавливаем темную тему
        ctk.set_default_color_theme("dark-blue")  # Устанавливаем темно-синюю цветовую схему
        
        print("Создание приложения...")
        app = App()
        print("Приложение создано успешно, запуск главного цикла...")
        app.mainloop()
        print("Приложение завершено")
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        traceback.print_exc()