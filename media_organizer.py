import os, sys
from shutil import move
from hashlib import md5
from PIL import Image
from PIL.ExifTags import TAGS
from tkinter import Tk, Button, Label, filedialog, Checkbutton, Text, Scrollbar, BooleanVar, Frame
from tkinter import SUNKEN, BOTTOM, E, X, END

class MediaOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("照片整理简易工具 v0.2")
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, "favicon.ico")
        self.root.iconbitmap(icon_path)
        self.selected_folder = None
        self.tmp = ""
        self.md5_hashes = set()  # 存储已处理文件的MD5值

        self.create_widgets()

    def create_widgets(self):
        # 创建Frame来组织复选框和按钮
        control_frame = Frame(self.root)
        control_frame.pack(pady=10)
        # 创建选择文件夹的按钮
        select_button = Button(control_frame, text="选择文件夹", command=self.select_folder)
        select_button.pack(side='left', padx=5)

        # 创建复选框
        self.md5_var = BooleanVar()
        self.md5_check = Checkbutton(control_frame, text='MD5校验', variable=self.md5_var)
        self.md5_check.pack(side='left', padx=5)

        # 绑定鼠标事件
        self.md5_check.bind("<Enter>", lambda event: self.show_tooltip(event, self.md5_check))
        self.md5_check.bind("<Leave>", self.hide_tooltip)

        # 创建开始按钮
        start_button = Button(control_frame, text="开始整理", command=self.start_organizing)
        start_button.pack(side='left', padx=5)

        # 创建状态标签

        self.status_label = Label(self.root, text="""将所选文件夹中的媒体文件按照年月分别整理到不同文件夹（例如 202411）中\n需要媒体文件包含EXIF信息，仅整理所选文件夹中的文件，不包含子文件夹\n目前处理的照片支持格式有：.png, .jpg, .jpeg, .tiff, .bmp, .gif""", height=3)
        self.status_label.pack(pady=10)

        # 创建文本框
        log_frame = Frame(self.root)
        log_frame.pack(pady=10, fill='both', expand=True)

        self.log_text = Text(log_frame, height=20, width=80)
        self.log_text.pack(side='left', fill='both', expand=True)

        scrollbar = Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')

        self.log_text.config(yscrollcommand=scrollbar.set)

        # 状态栏
        self.statusbar = Label(self.root, text="ssdreamC 版权所有，52PoJie 免费提供 ", bd=1, relief=SUNKEN, anchor=E)
        self.statusbar.pack(side=BOTTOM, fill=X)

    def check_md5(self, file_path):
        """ 计算文件的MD5值并检查是否已存在 """
        with open(file_path, 'rb') as f:
            md5_hash = md5(f.read()).hexdigest()
        if self.md5_var.get():  # 如果启用了MD5校验
            if md5_hash in self.md5_hashes:
                self.log_text.insert(END, f"跳过重复文件：{file_path}\n")
                self.log_text.see(END)
                self.root.update_idletasks()
                return False
            self.md5_hashes.add(md5_hash)
        return True
    
    def get_exif_data(self, image_path):
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            if exif_data is None:
                return None
            exif = {
                TAGS[k]: v
                for k, v in exif_data.items()
                if k in TAGS
            }
            return exif
        except Exception as e:
            self.log_text.insert(END, f"读取EXIF数据失败: {e}\n")
            
            self.log_text.see(END)
            self.root.update_idletasks()  # 强制更新界面
            return None

    def get_date_taken(self, exif_data):
        return exif_data.get('DateTimeOriginal', None)

    def organize_photos(self, folder_path, file_types):
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in file_types):
                file_path = os.path.join(folder_path, filename)
                if not self.check_md5(file_path):
                    continue
                exif_data = self.get_exif_data(file_path)
                if exif_data:
                    date_taken = self.get_date_taken(exif_data)
                    if date_taken:
                        year_month = date_taken[:7].replace(':', '')
                        year_month_folder = os.path.join(folder_path, year_month)
                        if not os.path.exists(year_month_folder):
                            os.makedirs(year_month_folder)
                        move(file_path, os.path.join(year_month_folder, filename))
                        self.log_text.insert(END, f"移动 {filename} 到 {year_month_folder}\n")
                        
                        self.log_text.see(END)
                        self.root.update_idletasks()  # 强制更新界面
                    else:
                        self.log_text.insert(END, f"没有日期数据的文件： {filename}\n")
                        
                        self.log_text.see(END)
                        self.root.update_idletasks()  # 强制更新界面
                else:
                    self.log_text.insert(END, f"没有EXIF的文件： {filename}\n")
                    
                    self.log_text.see(END)
                    self.root.update_idletasks()  # 强制更新界面

    def select_folder(self):
        self.selected_folder = filedialog.askdirectory()
        if self.selected_folder:
            self.status_label.config(text=f"选择了文件夹:\n{self.selected_folder}")

    def start_organizing(self):
        if self.selected_folder:
            file_types = []
            file_types.extend(['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'])
            self.organize_photos(self.selected_folder, file_types)
            self.status_label.config(text=f"{self.selected_folder}\n中的文件整理好了。")
        else:
            self.status_label.config(text="请选择一个文件夹。")

    def show_tooltip(self, event, widget):
        self.tmp = self.status_label.cget("text")
        if widget == self.md5_check:
            self.status_label.config(text="启用MD5校验以避免重复文件，启用后整理速度会变慢")

    def hide_tooltip(self, event):
        self.status_label.config(text=self.tmp)

if __name__ == "__main__":
    root = Tk()
    app = MediaOrganizer(root)
    root.mainloop()