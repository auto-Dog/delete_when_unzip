import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
# import subprocess
import threading
from delete_when_unzip import main_unzip as single_unzip
from delete_when_unzip_multi import main_unzip as multi_unzip
import time
import os
import re

def thread_it(func, *args):
    '''将函数打包进线程'''
    # 创建
    t = threading.Thread(target=func, args=args) 
    t.setDaemon(True) 
    # 启动
    t.start()

class ProcessManager:
    '''
    采用进程控制类，在后台运行主解压进程和进度条进程。
    解压前将文件名等参数传给该对象，开始解压时调用run()方法
    '''
    def __init__(self,mode:str,file_path:str,chunksize:int,password_str:str):
        self.mode = mode
        self.file_path = file_path
        self.chunksize = chunksize
        self.password_str = password_str
        self.fsize = 0

    def run(self):
        '''开始解压，启动进程（非阻塞），并返回'''
        self.progress_bar = ttk.Progressbar(window, orient='horizontal', length=200, mode='determinate')
        self.progress_bar.pack(pady=10)
        thread_it(self.pack_process)
        thread_it(self.process_inquiry)

    def pack_process(self):
        '''
        解压主进程
        '''
        try:
            if self.mode == 'mode1':
                unzip_func = single_unzip
                self.fsize = os.path.getsize(self.file_path)*1.0
            if self.mode == 'mode2':
                unzip_func = multi_unzip
                self.fsize = self.get_multi_filecounts()*1.0
            unzip_func(self.file_path,self.chunksize,self.password_str)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.end_process()

    def process_inquiry(self):
        '''
        管理进度条进度的进程。每隔0.1s更新一次进度值。其中采取了平滑的进度估计方法。
        进度达到100后，解锁界面
        '''
        if self.fsize == 0: # 获取文件大小后才会执行
            return
        self.progress_bar['value'] = 1.0
        velocity_bar = 0.1 # 0.1% per step -> 1% per sec
        bar_top = 1.0
        last_val = 0.0
        new_val = 0.0
        delta_n = 1
        first_checkpoint_limit = 20
        # 匀速更新进度条
        while True:
            if self.mode == 'mode1':
                try:
                    new_val = 100.0 * (self.fsize-os.path.getsize(self.file_path))/self.fsize
                except:
                    new_val = 100.0 # 处理完最后一个块后文件已经不存在,直接拉到100%进度
            if self.mode == 'mode2':
                new_val = 100.0 * (self.fsize-self.get_multi_filecounts()) / self.fsize
            if new_val==100:
                break
            # 第一次更新进度条前并不知道进度条实际速度，预估值0.1可能偏大。故条进度条大于某一阈值且一直没有收到进度更新时，停止进度
            if bar_top>=first_checkpoint_limit: 
                velocity_bar = 0.0
            bar_top = bar_top + velocity_bar
            if new_val != last_val: # 获得新进度，更新速度和bar参数，取消限制
                velocity_bar = abs(new_val-last_val)/delta_n
                bar_top = new_val
                last_val = new_val
                first_checkpoint_limit = 100
                delta_n = 0
            # 更新进度条
            self.progress_bar['value'] = bar_top
            self.progress_bar.update()
            time.sleep(0.1)
            delta_n+=1
        messagebox.showinfo("Successfully Unzipped!","Successfully Unzipped!")
        self.end_process()

    def get_multi_filecounts(self):
        '''
        查询分卷文件剩余数目
        '''
        file_list = []
        file_path,file_basename_zip = os.path.split(self.file_path)
        if file_path == '':
            file_path = './'
        file_basename,_ = os.path.splitext(file_basename_zip)
        files = os.listdir(file_path)
        # 筛出file_basename.zip, file_basename.z01, file_basename.z02 ...
        pattern1 = re.compile(rf"{re.escape(file_basename)}\.z\d+",re.I)
        pattern2 = re.compile(rf"{re.escape(file_basename)}\.zip",re.I)
        for file in files:
            if pattern1.match(file) or pattern2.match(file):
            # if file.startswith(file_basename) and os.path.isfile(os.path.join(file_path, file)):
                file_list.append(os.path.join(file_path, file)) # 将按照z01,z02,...zip顺序排列
        return len(file_list)

    def end_process(self):
        self.progress_bar['value'] = 100.0
        run_state.set(" 运行 ")      # global var
        run_button['state'] = 'normal'
        self.progress_bar.pack_forget()

def run_program():
    run_button['state'] = 'disable' # global var
    run_state.set("运行中...")      # global var
    file_path = file_entry.get()
    number = number_entry.get()
    number = eval(number)*1024*1024
    # number = str(number)
    mode = var_mode.get()

    if checkbox_var.get() == 1:
        password_str = password_entry.get()
    else:
        password_str = None

    process_unzip = ProcessManager(mode,file_path,number,password_str) # 采用多线程运行任务和控制进度条，非阻塞
    process_unzip.run() 
    # try:
    #     # 运行命令行程序
    #     if mode == 'mode1':
    #         single_unzip(file_path,number,password_str)

    #     elif mode == 'mode2':
    #         multi_unzip(file_path,number,password_str)

    #     messagebox.showinfo("Successfully Unzipped!","Successfully Unzipped!")
    # except Exception as e:
    #     messagebox.showerror("Error", str(e))
    # run_state.set(" 运行 ")      # global var
    # run_button['state'] = 'normal'

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[('ZIP Files','.zip'),('All Files','*')])
    file_entry.delete(0, tk.END)
    file_entry.insert(0, file_path)

# 创建主窗口
window = tk.Tk()
window.title("Delete when unzip(For BIIIIG zip file)")
window.iconbitmap('app_icon.ico')

# 创建文件路径输入框和浏览按钮
file_label = tk.Label(window, text="文件路径:")
file_label.pack()
file_entry = tk.Entry(window, width=50)
file_entry.pack()
browse_button = tk.Button(window, text="选择文件", command=browse_file)
browse_button.pack()

# 创建chunksize数值框
number_label = tk.Label(window, text="Chunk size (MB):")
number_label.pack()
# number_entry = tk.Entry(window)
# number_entry.insert(0, "512")
default_chunksize = tk.StringVar()
default_chunksize.set(512)
number_entry = tk.Spinbox(window,from_=0,to=1e12,textvariable=default_chunksize)
number_entry.pack()

# 创建密码输入框
def toggle_entry_state():
    if checkbox_var.get() == 1:
        password_entry.config(state=tk.NORMAL)
    else:
        password_entry.config(state=tk.DISABLED)
checkbox_var = tk.IntVar()
checkbox = tk.Checkbutton(window, text="使用密码", variable=checkbox_var, command=toggle_entry_state)
checkbox.pack()

password_entry = tk.Entry(window, state=tk.DISABLED)
password_entry.pack()

# 创建模式选择区
label_mode = tk.Label(window, text="选择模式:")
label_mode.pack()
var_mode = tk.StringVar()
radio_mode1 = tk.Radiobutton(window, text="单个压缩文件", variable=var_mode, value="mode1")
radio_mode1.pack()
radio_mode2 = tk.Radiobutton(window, text="分卷压缩文件", variable=var_mode, value="mode2")
radio_mode2.pack()
var_mode.set("mode1")

# 创建运行按钮
run_state = tk.StringVar()
run_state.set(" 运行 ")
run_button = tk.Button(window, textvariable=run_state, command=run_program)
run_button.pack()

# 运行主循环
window.mainloop()