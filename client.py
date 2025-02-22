import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, scrolledtext
import socket
import threading
from io import BytesIO
from PIL import Image, ImageTk, ImageFile
import datetime

# 서버 설정
SERVER_IP = 'server'
SERVER_PORT = 8080
SERVER_ADDR = (SERVER_IP, SERVER_PORT)

# 청크
CHUNK_SIZE = 1024

class Client:
    def __init__(self, root) -> None:
        self.root = root
        self.ui = self.initialize_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        # 변수 선언
        self.file_path = ''
        self.is_sending = False

    # 프로그램의 UI 초기화
    def initialize_ui(self) -> dict:
        # 메세지 출력용(수정 불가) 스크롤 텍스트 박스 및 캔버스
        canvas = tk.Canvas(self.root, width=600, height=400)
        canvas.grid(row=0, column=0, padx=10, pady=10)

        msg_view = scrolledtext.ScrolledText(self.root, width=100, height=30, state=tk.DISABLED)
        msg_view.grid(row=0, column=1, padx=10, pady=10)

        # 버튼들
        file_button = tk.Button(self.root, text='이미지 선택', command=self.select_file)
        file_button.grid(row=1, column=0, padx=10, pady=5)

        send_button = tk.Button(self.root, text='서버로 전송', command=self.send_data)
        send_button.grid(row=1, column=1, padx=10, pady=5)

        exit_button = tk.Button(self.root, text='종료', command=self.close)
        exit_button.grid(row=1, column=2, padx=10, pady=5)

        return {
            "canvas": canvas,
            "msg_view": msg_view,
            "file_button": file_button,
            "send_button": send_button,
            "exit_button": exit_button
        }

    # 서버로 전송할 이미지 선택
    def select_file(self) -> None:
        file_path = filedialog.askopenfilename(
            initialdir='/app',
            title='이미지 파일 선택',
            filetypes=[('이미지 파일', '*.jpg *.jpeg')]
        )
        if file_path:
            self.file_path = file_path
            self.display_msg(f'선택된 파일: {file_path}', 'msg')

            try:
                image = Image.open(file_path)
                self.display_image(image)
            except Exception as e:
                self.display_msg(f'이미지 로딩 오류: {str(e)}', 'error')
    
    # 이미지 표시
    def display_image(self, image: Image.Image) -> None:
        image.thumbnail((600, 400))
        img = ImageTk.PhotoImage(image)
        self.ui["canvas"].create_image(300, 200, image=img)
        self.ui["canvas"].image = img
    
    # 서버로 데이터 전송
    def send_data(self) -> None:
        if not self.file_path:
            self.display_msg('파일을 선택한 후 전송 버튼을 누르세요.', 'error')
            return

        try:
            self.is_sending = True

            with open(self.file_path, 'rb') as file:
                data = file.read()
                total_size = len(data)

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((SERVER_IP, SERVER_PORT))
                    sock.sendall(total_size.to_bytes(8, 'big'))

                    for i in range(0, total_size, CHUNK_SIZE):
                        sock.sendall(data[i:i+CHUNK_SIZE])
                    self.display_msg('이미지 전송 완료', 'msg')
                    
                    sock.settimeout(10)
                    response = sock.recv(1024)
                    if response:
                        self.display_msg(response.decode('utf-8'), 'msg')
                    else:
                        self.display_msg('서버로부터 응답이 없습니다.', 'error')
        except Exception as e:
            self.display_msg(f'데이터 전송 오류: {e}', 'error')
        finally:
            self.is_sending = False
    
    # Quit
    def close(self) -> None:
        if self.is_sending:
            messagebox.showinfo('통신중', '통신 종료 후 다시 시도하세요')
            return
        self.root.quit()
    
    # 로그 출력
    def display_msg(self, message: str, msg_type: str = "msg") -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        format_msg = f"[{timestamp}][{msg_type}] {message}\n"

        self.ui["msg_view"].config(state=tk.NORMAL)
        self.ui["msg_view"].insert(tk.END, format_msg)
        self.ui["msg_view"].yview(tk.END)
        self.ui["msg_view"].config(state=tk.DISABLED)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('클라이언트')
    root.resizable(False, False)

    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="NanumGothic", size=12)
    root.option_add("*Font", default_font)

    app = Client(root)
    root.mainloop()