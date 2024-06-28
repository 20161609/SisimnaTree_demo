import tkinter as tk
import lib_sanitizer as Df
from lib_branch import get_paths
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import os


class ImageSaver:
    def __init__(self, sync_function, branch_path='Home'):
        self.sync = sync_function  # 동기화 함수
        self.branch_path = branch_path  # 현재 브랜치 경로
        self.root = tk.Tk()  # 메인 윈도우

        # 불러온 이미지 경로
        self.file_path = None

        # 입력 세션
        self.date_entry = None
        self.in_entry, self.out_entry = None, None
        self.branch_dropdown = None
        self.description_entry = None

        # 이미지 데이터 및 뷰어
        self.img = None
        self.large_image_window = None
        self.panel = None
        try:
            self.make_window()
        except Exception as e:
            messagebox.showinfo("Fail", str(e))
            self.root.destroy()

    def make_window(self):  # 창 UI 구성
        self.root.title("Photo Upload and Data Entry Example")
        self.root.grid_anchor("center")

        # 창 크기 설정 및 화면 가운데로 배치
        window_width, window_height = 600, 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        position_top = 0
        position_right = int(screen_width / 2 - window_width / 2)
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

        # ttk 스타일
        style = ttk.Style(self.root)
        style.configure('TLabel', font=('Arial', 12))
        style.configure('TButton', font=('Arial', 12))

        # 기본 이미지 설정
        self.img = Image.new("RGB", (200, 200), (192, 192, 192))

        # 이미지 업로드 섹션
        self.panel = ttk.Label(self.root, anchor="center")
        self.panel.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        upload_button = ttk.Button(self.root, text="Upload Photo", command=self.upload_photo)
        upload_button.grid(row=1, column=0, columnspan=2, pady=10)

        # 데이터 입력 필드 구성
        ttk.Label(self.root, text="Date:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.date_entry = ttk.Entry(self.root, width=48)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5)

        # input 브랜치 명
        ttk.Label(self.root, text="Branch:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        branch_var = tk.StringVar()
        branch_var.set(self.branch_path)
        branch_options = get_paths()
        self.branch_dropdown = ttk.Combobox(
            self.root,
            textvariable=branch_var,
            width=45,
            values=branch_options,
            state="readonly")
        self.branch_dropdown.grid(row=3, column=1, padx=5, pady=5)

        # Input 내역
        ttk.Label(self.root, text="In:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        self.in_entry = ttk.Entry(self.root, width=48)
        self.in_entry.grid(row=4, column=1, padx=5, pady=5)

        # Input 지출 내역
        ttk.Label(self.root, text="Out:").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        self.out_entry = ttk.Entry(self.root, width=48)
        self.out_entry.grid(row=5, column=1, padx=5, pady=5)

        # Input 상세 내역
        ttk.Label(self.root, text="Description:").grid(row=6, column=0, sticky='e', padx=5, pady=5)
        self.description_entry = tk.Entry(self.root, width=48)
        self.description_entry.grid(row=6, column=1, padx=5, pady=5)

        # 이미지 및 정보 저장
        save_button = ttk.Button(self.root, text="SAVE", command=self.save_data)
        save_button.grid(row=7, column=0, columnspan=2, pady=10)
        panel_image = ImageTk.PhotoImage(self.img)
        self.panel.config(image=panel_image)
        self.panel.image = panel_image
        self.root.mainloop()

    def upload_photo(self):  # 이미지 업로드
        self.file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if self.file_path:
            # 이미지 불러 오기
            self.img = Image.open(self.file_path)

            # 이미지 프레임 창
            self.show_large_image()

            # 패널 이미지 구현
            self.img.thumbnail((250, 250))
            panel_image = ImageTk.PhotoImage(self.img)
            self.panel.config(image=panel_image)
            self.panel.image = panel_image

    def show_large_image(self):  # 이미지 프레임 창
        # 타이틀 및 이미지 설정
        if self.large_image_window is not None:
            self.large_image_window.destroy()

        self.large_image_window = tk.Toplevel(self.root)
        self.large_image_window.title("Large Image View")

        # canvas 설정
        canvas = tk.Canvas(self.large_image_window)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scrollbar = ttk.Scrollbar(self.large_image_window, orient=tk.VERTICAL, command=canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        h_scrollbar = ttk.Scrollbar(self.large_image_window, orient=tk.HORIZONTAL, command=canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # canvas 이미지 구성
        image_tk = ImageTk.PhotoImage(self.img)
        canvas.create_image(0, 0, anchor="nw", image=image_tk)
        canvas.image = image_tk
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        # 스크린 비율 및 크기 설정
        screen_width = 800  # self.root.winfo_screenwidth()
        screen_height = 800  # self.root.winfo_screenheight()
        self.large_image_window.geometry(f"{screen_width}x{screen_height}")

        # 방향키 스크롤 설정
        self.large_image_window.bind("<Left>", lambda e: canvas.xview_scroll(-1, "units"))
        self.large_image_window.bind("<Right>", lambda e: canvas.xview_scroll(1, "units"))
        self.large_image_window.bind("<Up>", lambda e: canvas.yview_scroll(-1, "units"))
        self.large_image_window.bind("<Down>", lambda e: canvas.yview_scroll(1, "units"))
        self.large_image_window.focus_set()

    def save_data(self):  # 이미지 및 Transaction 정보 저장
        # 입력 유효성 검사
        # 날짜 입력
        _date = Df.format_date(self.date_entry.get().strip())

        # 브랜치 입력
        _branch = self.branch_dropdown.get().strip().replace('/', '-')

        # 캐시 트랜젝션 입력
        try:
            _in = self.in_entry.get().strip() or '0'
            _out = self.out_entry.get().strip() or '0'
            _cashflow = int(_in) - int(_out)
        except:
            messagebox.showinfo("Fail", "Invalid input for cash flow. Please enter numeric values.")
            return

        # 설명 입력
        _description = self.description_entry.get().strip()

        info = Df.make_image_file_name(_date, _branch, _cashflow, _description)
        if info['status']:  # 유효한 입력
            try:
                # 저장
                if self.file_path:
                    self.img = Image.open(self.file_path)

                save_path = f"transactions/{info['tag']}.png"
                self.img.save(save_path)
                self.root.destroy()
                self.sync()
                messagebox.showinfo("Success", "Data saved successfully")
            except Exception as e:
                messagebox.showinfo("Fail", str(e)+'fuck you')
        else:  # 유효 하지 않은 입력 (에러 메시지 출력)
            messagebox.showinfo("Fail", info['txt'])
