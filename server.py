import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, scrolledtext
import socket
import threading
import tensorflow as tf
import numpy as np
import pandas as pd
from io import BytesIO
from PIL import Image, ImageTk, ImageFile
import datetime

# 사전에 학습한 모델+라벨을 불러오기
model = tf.saved_model.load('./model_512x512')
label = './label.xlsx'
df = pd.read_excel(label)

# 서버 설정 (only local)
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8080
SERVER_ADDR = (SERVER_IP, SERVER_PORT)

class Server:
    def __init__(self, root) -> None:
        self.root = root
        self.ui = self.initialize_ui(self.root, self.stop_server)

        # 서버 & 스레드 초기화
        self.server_socket = None
        self.client_threads = []
        self.client_sockets = []
        self.running = False

        # 서버 실행
        self.start_server()
    
    # 프로그램의 UI 초기화
    def initialize_ui(self, root: tk.Tk, stop_server_callback) -> dict:
        # 메세지 출력용(수정 불가) 스크롤 텍스트 박스
        msg_view = scrolledtext.ScrolledText(root, width=80, height=30)
        msg_view.config(state=tk.DISABLED)
        msg_view.grid(row=0, column=0, padx=10, pady=5)

        # 종료 버튼
        exit_button = tk.Button(root, text='서버 종료', command=stop_server_callback)
        exit_button.grid(row=1, column=0, padx=10, pady=5)

        return {
            "msg_view": msg_view,
            "exit_button": exit_button
        }
    
    # 서버 실행
    def start_server(self) -> None:
        if self.running:
            self.display_msg("서버가 이미 실행중입니다.", "error")
            return
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(SERVER_ADDR)
            self.server_socket.listen(socket.SOMAXCONN)
            self.server_socket.settimeout(1)

            self.running = True
            self.display_msg(f'서버 실행됨: {SERVER_IP}:{SERVER_PORT}', 'msg')
            
            # 비동기 클라이언트 연결 대기
            threading.Thread(target=self.listen_for_clients, daemon=True).start()
        except Exception as e:
            self.display_msg(f'서버 실행 실패: {str(e)}', 'error')

    # 클라이언트 연결 대기
    def listen_for_clients(self) -> None:
        while self.running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                self.client_sockets.append(client_socket)
                self.display_msg(f'클라이언트 연결: {client_addr}', 'msg')
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_addr)
                )
                self.client_threads.append(client_thread)
                client_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.display_msg(f'클라이언트 연결 중 오류: {str(e)}', 'error')
    
    # 클라이언트 처리
    def handle_client(self, client_socket: socket.socket, client_addr: tuple) -> None:
        try:
            self.display_msg(f'처리 함수 실행됨!', 'msg')

        except Exception as e:
            self.display_msg(f'처리 함수 실행중 오류!', 'error')
        
        finally:
            # 소켓 닫기 (연결 해제)
            try:
                client_socket.close()
            except Exception as e:
                self.display_msg(f'연결 해제 오류: {str(e)}', 'error')
            
            # 소켓, 스레드 제거
            if client_socket in self.client_sockets:
                try:
                    self.client_sockets.remove(client_socket)
                except ValueError:
                    self.display_msg(f'이미 제거된 소켓입니다: {client_addr}', 'error')
            
            current_thread = threading.current_thread()
            if current_thread in self.client_threads:
                try:
                    self.client_threads.remove(current_thread)
                except ValueError:
                    self.display_msg(f'이미 제거된 스레드입니다: {current_thread.name}', 'error');
            self.display_msg(f'클라이언트 연결 해제됨: {client_addr}', 'msg')
            
            
    # Quit
    def stop_server(self) -> None:
        if not self.running:
            self.root.quit()
            return
        
        if messagebox.askokcancel("서버 종료", "종료하시겠어요?"):
            self.running = False
            self.display_msg("서버를 종료하는 중...", "msg")

            # 모든 클라이언트 소켓 닫기
            for client_socket in self.client_sockets:
                try:
                    client_socket.close()
                except Exception as e:
                    self.display_msg(f'클라이언트 소켓 닫기 오류: {str(e)}', 'error')
            
            # 모든 클라이언트 스레드 종료
            for thread in self.client_threads:
                if thread.is_alive():
                    thread.join(timeout=1)
            
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception as e:
                    self.display_msg(f'서버 소켓 닫기 오류: {str(e)}', 'error')

            self.root.quit()

    # 로그 출력
    def display_msg(self, message: str, msg_type: str = "msg") -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        format_msg = f"[{timestamp}][{msg_type}] {message}\n"

        self.ui["msg_view"].config(state=tk.NORMAL)
        self.ui["msg_view"].insert(tk.END, format_msg)
        self.ui["msg_view"].yview(tk.END)
        self.ui["msg_view"].config(state=tk.DISABLED)

# RUN
if __name__ == '__main__':
    root = tk.Tk()
    root.title('서버')
    root.resizable(False, False)

    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="NanumGothic", size=12)
    root.option_add("*Font", default_font)

    server_app = Server(root)
    root.mainloop()