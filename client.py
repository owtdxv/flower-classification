import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, scrolledtext
import socket
import threading
from io import BytesIO
from PIL import Image, ImageTk, ImageFile
import datetime

# 서버 설정 (only local)
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8080
SERVER_ADDR = (SERVER_IP, SERVER_PORT)

class Client:
    def __init__(self, root) -> None:
        pass

if __name__ == '__main__':
    root = tk.Tk()
    root.title('서버')
    root.resizable(False, False)

    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="NanumGothic", size=12)
    root.option_add("*Font", default_font)

    app = Client(root)
    root.mainloop()