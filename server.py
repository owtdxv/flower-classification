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

# 서버 설정
SERVER_IP = '0.0.0.0'
SERVER_PORT = 8080
SERVER_ADDR = (SERVER_IP, SERVER_PORT)

class Server:
    def __init__(self, root) -> None:
        self.root = root
        self.ui = self.initialize_ui(self.root, self.stop_server)
        self.root.protocol("WM_DELETE_WINDOW", self.stop_server)

        # 서버 & 스레드 초기화
        self.server_socket = None
        self.client_threads = []
        self.client_sockets = []
        self.running = False

        # 사전 학습된 모델과 라벨 파일 로드
        try:
            self.model = tf.saved_model.load('./model_512x512')
            self.df = pd.read_excel('./label.xlsx')  # 라벨 파일 경로 (컬럼: 'en_class', 'ko_class')
            self.infer = self.model.signatures['serving_default']
            self.display_msg("모델 및 라벨 로드 성공", "msg")
        except Exception as e:
            self.display_msg(f"모델 또는 라벨 로드 실패: {str(e)}", "error")

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
    
    # 이미지 전처리: 이미지를 numpy 배열로 변환
    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image = image.resize((299, 299))
        arr = np.array(image) / 255.0
        arr = np.expand_dims(arr, axis=0)
        return arr
    
    # 이미지 분류 함수: 전처리 후 모델을 통해 예측값 반환
    def classify_image(self, image: Image.Image) -> np.ndarray:
        preprocessed_image = self.preprocess_image(image)
        input_tensor = tf.convert_to_tensor(preprocessed_image, dtype=tf.float32)
        prediction = self.infer(input_tensor)
        output_key = list(self.infer.structured_outputs.keys())[0]
        return prediction[output_key].numpy()
    
    # 예측된 인덱스에 따른 꽃 이름 반환 (영문, 한글)
    def get_flower_names_by_index(self, index: int):
        return (self.df.iloc[index]['en_class'], self.df.iloc[index]['ko_class'])
    
    # 클라이언트 처리
    def handle_client(self, client_socket: socket.socket, client_addr: tuple) -> None:
        try:
            self.display_msg(f'클라이언트 처리 시작: {client_addr}', 'msg')
            
            # 8바이트로 데이터 크기 수신
            data_size_bytes = client_socket.recv(8)
            if not data_size_bytes:
                self.display_msg("데이터 크기 수신 실패", "error")
                return
            expected_size = int.from_bytes(data_size_bytes, 'big')
            self.display_msg(f'예상 데이터 크기: {expected_size} bytes', 'msg')
            
            # 실제 데이터 수신
            received_data = b''
            while len(received_data) < expected_size:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                received_data += chunk
            self.display_msg(f'수신된 데이터 크기: {len(received_data)} bytes', 'msg')
            
            if len(received_data) != expected_size:
                self.display_msg("수신 데이터 크기가 예상과 다릅니다.", "error")
                return

            # 수신한 데이터를 이미지로 변환
            try:
                image = Image.open(BytesIO(received_data))
                self.display_msg("이미지 로드 성공", "msg")
            except Exception as e:
                self.display_msg(f"이미지 로드 실패: {str(e)}", "error")
                return
            
            # 이미지 분류 수행
            try:
                prediction = self.classify_image(image)
                predicted_class_idx = np.argmax(prediction[0])
                self.display_msg(f'예측 결과: {prediction}', 'msg')
                self.display_msg(f'예측 인덱스: {predicted_class_idx}', 'msg')
                en_label, ko_label = self.get_flower_names_by_index(predicted_class_idx)
                result = f'이 꽃은 {ko_label}({en_label})인 것 같아요!'
                self.display_msg(f'분류 결과: {result}', 'msg')
            except Exception as e:
                self.display_msg(f'이미지 분류 실패: {str(e)}', 'error')
                result = "이미지 분류에 실패했습니다."
            
            # 클라이언트에 결과 전송
            client_socket.sendall(result.encode('utf-8'))
        except Exception as e:
            self.display_msg(f'처리 중 오류 발생: {str(e)}', 'error')
        finally:
            try:
                client_socket.close()
            except Exception as e:
                self.display_msg(f'클라이언트 소켓 닫기 실패: {str(e)}', 'error')
            if client_socket in self.client_sockets:
                self.client_sockets.remove(client_socket)
                
            current_thread = threading.current_thread()
            if current_thread in self.client_threads:
                self.client_threads.remove(current_thread)
            self.display_msg(f'클라이언트 연결 종료됨: {client_addr}', 'msg')
            
            
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