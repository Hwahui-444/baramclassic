import pytesseract  
from PIL import ImageGrab, ImageEnhance, ImageFilter  
import tkinter as tk  
import threading  
import time  
import json  
import pynput  
import pyautogui  
import os
from tkinter import messagebox
import platform
import sys
import subprocess

def check_tesseract_installed():
    # macOS에서는 일반적으로 /usr/local/bin/tesseract 경로에 설치됨
    tesseract_path = '/usr/local/bin/tesseract'

    # Tesseract가 설치되어 있는지 확인
    if not os.path.exists(tesseract_path):  # 설치되지 않으면
        print("Tesseract가 설치되지 않았습니다. 설치를 시작합니다...")
        install_tesseract()  # 설치 함수 호출
    else:
        print("Tesseract가 설치되어 있습니다.")

    return tesseract_path

def install_tesseract():
    # Homebrew가 설치되어 있는지 확인
    try:
        result = subprocess.run(['which', 'brew'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Homebrew가 설치되어 있지 않습니다. 설치가 필요합니다.")
            print("https://brew.sh에서 Homebrew를 설치해 주세요.")
            return  # Homebrew가 없으면 종료하지 않고 설치를 중단
    except Exception as e:
        print(f"Homebrew 확인 중 오류 발생: {e}")
        return  # 오류가 발생하면 설치를 중단

    try:
        print("Homebrew를 사용하여 Tesseract를 설치합니다...")
        ## subprocess.run(['brew', 'install', 'tesseract'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Tesseract 설치 중 오류 발생: {e}")
        return  # 설치 오류가 발생하면 중단

def set_tesseract_path():
    if getattr(sys, 'frozen', False):  # EXE 파일에서 실행 중일 때
        tesseract_path = os.path.join(sys._MEIPASS, 'tesseract')
    else:  # 개발 환경에서 실행 중일 때
        # Tesseract가 설치된 경로를 확인하고 가져옵니다
        tesseract_path = check_tesseract_installed()

    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"Tesseract 경로 설정 완료: {tesseract_path}")

# Tesseract 경로 설정
set_tesseract_path()



class TimerApp:
    def __init__(self, root):
        
        self.root = root
        self.root.title("화희의 헬파 타이머 V4")  
        self.root.geometry("300x200")  
        self.root.resizable(False, False)  

        self.timer = 8.5
        self.remaining_time = self.timer
        self.is_running = False
        self.saved_key = "1"
        self.last_input_time = None
        self.always_on_top_var = tk.BooleanVar(value=False)

        self.x1, self.y1, self.x2, self.y2 = 0, 0, 300, 300

        self.detection_attempts = 3

        self.skill_key_pressed = False
        self.enter_key_pressed = False
        self.hellfire_detected = False

        self.is_timer_running = False
        self.load_settings()

        self.timer_label = tk.Label(root, text=f"{self.timer:.1f}초", font=("Arial", 40), fg="black")
        self.timer_label.pack(expand=True)

        self.options_button = tk.Button(root, text="옵션", command=self.open_options_window)
        self.options_button.pack(side="bottom", pady=10)

        self.start_key_listener()

        self.toggle_always_on_top()

    def open_options_window(self):
        if hasattr(self, 'options_window') and self.options_window.winfo_exists():
            self.options_window.destroy()

        # 옵션창 위치 설정
        window_x, window_y = self.root.winfo_x(), self.root.winfo_y()
        options_window_x = window_x
        options_window_y = window_y + self.root.winfo_height() + 30

        # 옵션창 생성
        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("옵션")
        self.options_window.geometry(f"300x250+{options_window_x}+{options_window_y}")
        self.options_window.resizable(False, False)

        # 라벨과 입력 필드 설정
        fields = [
            ("스킬 키를 입력하세요:", self.saved_key, "textbox"),
            ("타이머 값:", str(self.timer), "timer_entry"),
            ("메세지 검출 횟수:", str(self.detection_attempts), "detection_attempts_entry"),
            ("x1:", str(self.x1), "x1_entry"),
            ("y1:", str(self.y1), "y1_entry"),
            ("x2:", str(self.x2), "x2_entry"),
            ("y2:", str(self.y2), "y2_entry"),
        ]
        for i, (label_text, default_value, attr_name) in enumerate(fields):
            tk.Label(self.options_window, text=label_text).grid(row=i, column=0)
            entry = tk.Entry(self.options_window)
            entry.insert(0, default_value)
            entry.grid(row=i, column=1)
            setattr(self, attr_name, entry)

        # 항상 위 체크박스
        self.always_on_top_check = tk.Checkbutton(
            self.options_window, text="항상 위", variable=self.always_on_top_var, command=self.toggle_always_on_top_options
        )
        self.always_on_top_check.grid(row=len(fields), column=0, columnspan=2)
        self.toggle_always_on_top_options()

        # 마우스 좌표 표시 및 저장 버튼
        self.mouse_label = tk.Label(self.options_window, text="마우스 좌표: (0, 0)")
        self.mouse_label.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

        self.save_button = tk.Button(self.options_window, text="저장", command=self.save_options)
        self.save_button.grid(row=len(fields) + 2, column=0, columnspan=2, pady=10)

        self.update_mouse_coordinates()


    def update_mouse_coordinates(self):
        x, y = pyautogui.position()
        self.mouse_label.config(text=f"마우스 좌표: ({x}, {y})")
        self.options_window.after(100, self.update_mouse_coordinates)

    def toggle_always_on_top_options(self):
        if self.always_on_top_var.get():
            self.options_window.attributes("-topmost", True)
        else:
            self.options_window.attributes("-topmost", False)
        self.toggle_always_on_top()

    def save_settings(self):
        try:
            # 타이머 값 유효성 검사 및 변환
            self.timer = float(self.timer)
            if self.timer.is_integer():
                self.timer = int(self.timer)  # 정수로 변환

            # 메시지 검출 횟수 유효성 검사
            self.detection_attempts = int(self.detection_attempts_entry.get())
            if self.detection_attempts not in range(1, 4):
                raise ValueError("메세지 검출 횟수는 1~3까지 숫자만 입력 가능합니다.")

            # 설정 저장
            settings = {
                "saved_key": self.saved_key,
                "always_on_top": self.always_on_top_var.get(),
                "x1": self.x1,
                "y1": self.y1,
                "x2": self.x2,
                "y2": self.y2,
                "timer": self.timer,
                "detection_attempts": self.detection_attempts,
            }

            with open("settings_v4.json", "w") as file:
                json.dump(settings, file, indent=4)

            # 타이머 입력 필드 업데이트
            self.timer_entry.delete(0, tk.END)
            self.timer_entry.insert(0, str(self.timer))

            print("설정이 성공적으로 저장되었습니다.")

        except ValueError as ve:
            messagebox.showerror("오류", str(ve))
        except Exception as e:
            print(f"설정 저장 중 오류가 발생했습니다: {e}")

    def load_settings(self):
        try:
            # 현재 스크립트가 실행되는 디렉토리
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
            # 설정 파일의 절대 경로 생성
            settings_file = "settings_v4.json"
            settings_path = os.path.join(script_dir, settings_file)
        
            if os.path.exists(settings_path):  # 절대 경로로 파일 확인
                with open(settings_path, "r") as file:
                    settings = json.load(file)
                
                    # 설정 불러오기
                    self.saved_key = settings.get("saved_key", "1")
                    self.always_on_top_var.set(settings.get("always_on_top", False))
                    self.x1 = settings.get("x1", 0)
                    self.y1 = settings.get("y1", 0)
                    self.x2 = settings.get("x2", 300)
                    self.y2 = settings.get("y2", 300)
                    self.timer = settings.get("timer", 8.5)
                    self.detection_attempts = settings.get("detection_attempts", 3)
                
                print("설정이 성공적으로 불러와졌습니다.")
            else:
                print("설정 파일이 존재하지 않습니다. 기본값을 사용합니다.")
        except Exception as e:
            print(f"설정 불러오기 중 오류가 발생했습니다: {e}")

    def save_options(self):
        
        
        self.saved_key = self.textbox.get()
        self.x1 = int(self.x1_entry.get())
        self.y1 = int(self.y1_entry.get())
        self.x2 = int(self.x2_entry.get())
        self.y2 = int(self.y2_entry.get())
        self.timer = float(self.timer_entry.get())
        self.detection_attempts = int(self.detection_attempts_entry.get())

        
        self.save_settings()

        
        self.timer_label.config(text=f"{self.timer:.1f}초")

    def toggle_always_on_top(self):
        
        if self.always_on_top_var.get():
            self.root.attributes("-topmost", True)  
        else:
            self.root.attributes("-topmost", False)  

    def start_key_listener(self):
        
        listener = pynput.keyboard.Listener(on_press=self.on_key_press)
        listener.start()  

    def on_key_press(self, key):
        
        try:

            if self.is_timer_running:  
                return

            if hasattr(key, "char") and key.char == self.saved_key:
                self.skill_key_pressed = True
                self.last_input_time = time.time()
                print(f"스킬키 '{self.saved_key}' 입력됨 + 타이머:{self.remaining_time}")

            elif key == pynput.keyboard.Key.enter:  
                if self.skill_key_pressed and time.time() - self.last_input_time <= 4:  
                    print("엔터키 입력됨, 메시지 검출 시작")
                    self.root.after(500, self.detect_hellfire)  

        except AttributeError:
            pass  

    def detect_hellfire(self):

        image = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2))  
        results = []
        try:
            detection_attempts = self.detection_attempts
            if detection_attempts < 1:
                detection_attempts = 3  
        except ValueError:
            detection_attempts = 3  
        for attempt in range(detection_attempts):
            temp_image = image.convert("L")  
            if attempt == 0:
                enhancer_contrast = ImageEnhance.Contrast(temp_image)
                temp_image = enhancer_contrast.enhance(2)  
            elif attempt == 1:
                enhancer_brightness = ImageEnhance.Brightness(temp_image)
                temp_image = enhancer_brightness.enhance(1.2)  
            elif attempt == 2:
                temp_image = temp_image.filter(ImageFilter.SHARPEN)     
            result = pytesseract.image_to_string(temp_image, config="--psm 6", lang='kor').lower()  
            results.append(result)
        hellfire_messages = ['헬', '헬파', '헬파이', '헬파이어']
        self.hellfire_detected = any(message in result for result in results for message in hellfire_messages)
        print("OCR 결과:")
        for idx, result in enumerate(results):
            print(f"시도 {idx + 1}: {result.strip()}")
        print(f"헬파 메시지 감지 여부: {self.hellfire_detected}")
        if self.hellfire_detected:
            print("헬파 메시지 감지됨")
            self.run_timer()  
        else:
            print("헬파 메시지 없음")

    def run_timer(self):

        self.is_timer_running = True  
        self.timer_label.config(fg="red")  
        start_time = time.time()
        while time.time() - start_time < self.timer:  
            self.remaining_time = self.timer - (time.time() - start_time)
            self.timer_label.config(text=f"{self.remaining_time:.1f}초")
            self.root.update()  
            time.sleep(0.1)  
        self.is_timer_running = False  
        self.timer_label.config(fg="black")  
        self.timer_label.config(text=f"{self.timer:.1f}초")  


if __name__ == "__main__":
    root = tk.Tk()  
    app = TimerApp(root)  
    root.mainloop()  
