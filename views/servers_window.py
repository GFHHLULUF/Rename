import customtkinter as ctk
import tkinter as tk
from views.add_server import AddServerWindow
import tkinter.messagebox as msg

class ServersWindow():
    def __init__(self, master, app, db):
        
        self.master = master
        self.db = db
        self.app = app

        # Настройка темной темы для окна
        self.master.configure(fg_color="#1a1a1a")  # Очень темный фон

        self.master.title('Серверы')
        self.master.geometry('500x600+300+230')
        self.master.minsize(500, 600)

        self.scrollframe = ctk.CTkScrollableFrame(master=self.master, corner_radius=0, fg_color="transparent")
        self.scrollframe.pack(fill=ctk.BOTH, expand=True)

        self.innerframe = ctk.CTkFrame(self.scrollframe, fg_color="#2d2d2d")  # Темный фон
        self.innerframe.pack(expand=True)

        self.addserverbutton = ctk.CTkButton(self.innerframe, text='Добавить сервер', 
                                           command=self.open_add_server_window,
                                           fg_color="#4d4d4d", hover_color="#5d5d5d")
        self.addserverbutton.grid(row=1, column=1, pady=10, padx=10)

        self.serverframe = ctk.CTkFrame(self.innerframe, fg_color="#1a1a1a")  # Еще более темный фон
        self.serverframe.grid(row=2, column=1, pady=10, padx=10)

        self.serverslabels = []
        self.serversbuttons = []

        self.display_servers(self.db.servers)

    def display_servers(self, servers):
        frow = 1
        for server in servers:
            frow += 1
            label = ctk.CTkLabel(self.serverframe, text=f" {server}", text_color="#ffffff")
            label.grid(row=frow, column=1, pady=10, padx=10)
            self.serverslabels.append(label)

            delete_button = ctk.CTkButton(self.serverframe, text="Удалить", 
                                        command=lambda s=server: self.delete_server(s), 
                                        width=130, height=22, fg_color='#FF6D6A',
                                        hover_color='#FF5252')
            delete_button.grid(row=frow, column=2, pady=10, padx=10)
            self.serversbuttons.append(delete_button)
    
    def delete_server(self, server):
        result = msg.askquestion("Внимание", f"Вы уверены, что хотите удалить сервер: {server}")
        if result == "yes":
            try:
                self.db.delete_server(server)
                self.db.update_servers()
                self.app.update_servers()
                self.delete_server_wigets()
                self.display_servers(self.db.servers)
            except Exception as e:
                pass

    def delete_server_wigets(self):

        for label in self.serverslabels:
            label.destroy()
        self.serverslabels = []

        for button in self.serversbuttons:
            button.destroy()
        self.serversbuttons = []

    def open_add_server_window(self):
        add_server_window = ctk.CTkToplevel(self.master)
        add_server_window.title("Добавление сервера")

        AddServerWindow(add_server_window, self, self.app, self.db)
    