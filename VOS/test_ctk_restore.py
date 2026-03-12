import customtkinter as ctk
import threading
import time

class TestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x300")
        self.label = ctk.CTkLabel(self, text="Waiting...")
        self.label.pack(pady=20)
        
        self.after(5000, self.do_background_update)
        print("App started. Please minimize it now.")

    def do_background_update(self):
        print("Updating label in background...")
        self.label.configure(text=f"Updated at {time.ctime()}")
        # Schedule next
        self.after(5000, self.do_background_update)

if __name__ == "__main__":
    app = TestApp()
    app.mainloop()
