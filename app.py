
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
# import subprocess
import threading
from delete_when_unzip import main_unzip as single_unzip
from delete_when_unzip_multi import main_unzip as multi_unzip
from delete_when_unzip_rar import main_unzip as single_unzip_rar
from delete_when_unzip_rar_multi import main_unzip as multi_unzip_zc
from delete_when_unzip_cli import main_unzip as multi_unzip_rar
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
        self.modemap = {
            '单文件(single)，zip、tar.gz':0, 
            '单文件(single)，RAR':1, 
            '多文件(volumes)，zip':2,
            '多文件(volumes)，rar':3,
            '单文件，备选(single other)':4,
            '多文件，备选(volumes other)':5
        }
        self.mode = self.modemap[mode]
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
            if self.mode == 0:
                unzip_func = single_unzip
                self.fsize = os.path.getsize(self.file_path)*1.0
            if self.mode == 1:
                unzip_func = single_unzip_rar
                self.fsize = os.path.getsize(self.file_path)*1.0

            if self.mode == 2:
                unzip_func = multi_unzip
                self.fsize = self.get_multi_filecounts()*1.0
            if self.mode == 3:
                unzip_func = multi_unzip_rar
                self.fsize = self.get_multi_filecounts()*1.0

            if self.mode == 4:
                unzip_func = single_unzip_rar
                self.fsize = os.path.getsize(self.file_path)*1.0
            if self.mode == 5:
                unzip_func = multi_unzip_zc
                self.fsize = self.get_multi_filecounts()*1.0
            print(self.password_str)    # debug
            unzip_func(self.file_path,self.chunksize,self.password_str)
        except Exception as e:
            err_message = repr(e)
            print(err_message)
            if 'Rar!' in err_message or '7z' in err_message or 'UnsupportedCompressionTypeError(14)' in err_message:
                err_message = '不支持该类型文件(与文件加密算法有关)'
            if 'Decryption is unsupported' in err_message or\
                'Unsupported block header size' in err_message:
                err_message = 'libarchive暂不支持rar单文件有密码解压'
            if '\'str\' object cannot be interpreted as an integer' in err_message:
                err_message = '请使用对应的备选模式'
            messagebox.showerror("Error", err_message)
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
            if self.mode == 0 or self.mode == 1:
                try:
                    new_val = 100.0 * (self.fsize-os.path.getsize(self.file_path))/self.fsize
                except:
                    new_val = 100.0 # 处理完最后一个块后文件已经不存在,直接拉到100%进度
            if self.mode == 2 or self.mode == 3:
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
        if file_basename.endswith('.zip') or file_basename.endswith('.ZIP'):    # 针对.zip.00x多重分段文件
            file_basename,_ = os.path.splitext(file_basename)
        if file_basename.endswith('.part1'):    # 针对.part1.rar多重分段文件
            file_basename,_ = os.path.splitext(file_basename)
        files = os.listdir(file_path)
        # 筛出file_basename.zip, file_basename.z01, file_basename.z02 ...
        pattern1 = re.compile(rf"{re.escape(file_basename)}\.z\d+",re.I)
        pattern2 = re.compile(rf"{re.escape(file_basename)}\.zip",re.I)
        pattern3 = re.compile(rf"{re.escape(file_basename)}\.zip\.\d+",re.I)
        pattern4 = re.compile(rf"{re.escape(file_basename)}\.r\d+",re.I)
        pattern5 = re.compile(rf"{re.escape(file_basename)}\.rar",re.I)
        pattern6 = re.compile(rf"{re.escape(file_basename)}\.rar\.\d+",re.I)
        pattern7 = re.compile(rf"{re.escape(file_basename)}\.part\d+\.rar",re.I)
        for file in files:
            if pattern1.match(file) or pattern2.match(file) or pattern3.match(file) or\
                pattern4.match(file) or pattern5.match(file) or pattern6.match(file) or pattern7.match(file):
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
    file_path = filedialog.askopenfilename(filetypes=[('ZIP Files','.zip'),
                                                      ('ZIP Seg Files','.zip.001'),
                                                      ('RAR Files','.rar .part1.rar'),
                                                      ('All Files','*')])
    file_entry.delete(0, tk.END)
    file_entry.insert(0, file_path)

# 创建主窗口
window = tk.Tk()
window.title("Delete when unzip(For BIIIIG zip/rar file)")
window.iconbitmap('app_icon.ico')

# 创建文件路径输入框和浏览按钮
file_label = tk.Label(window, text="文件路径 (Path):")
file_label.pack()
file_entry = tk.Entry(window, width=50)
file_entry.pack()
browse_button = tk.Button(window, text="选择文件", command=browse_file)
browse_button.pack()

# 创建chunksize数值框
number_label = tk.Label(window, text="解压块大小 (Chunk size, MB):")
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
checkbox = tk.Checkbutton(window, text="使用密码(Password):", variable=checkbox_var, command=toggle_entry_state)
checkbox.pack()

password_entry = tk.Entry(window, state=tk.DISABLED)
password_entry.pack()

# 创建模式选择区
label_mode = tk.Label(window, text="选择模式(mode):")
label_mode.pack()
var_mode = tk.StringVar()
cbox = ttk.Combobox(window,textvariable=var_mode)
cbox['value'] = ('单文件(single)，zip、tar.gz', '单文件(single)，RAR', 
                 '多文件(volumes)，zip', '多文件(volumes)，rar',
                 '单文件，备选(single other)','多文件，备选(volumes other)')
cbox.pack()

# radio_mode1 = tk.Radiobutton(window, text="单个压缩文件", variable=var_mode, value="mode1")
# radio_mode1.pack()
# radio_mode2 = tk.Radiobutton(window, text="分卷压缩文件", variable=var_mode, value="mode2")
# radio_mode2.pack()
# var_mode.set("mode1")
# new_func_mode = tk.IntVar()
# new_func_mode_box = tk.Checkbutton(window, text="使用libarchive解压(支持大多压缩文件，\n但可能不稳定。解压RAR等必须选此模式)", variable=new_func_mode)
# new_func_mode_box.pack()

notice = tk.Label(window, text="(注意：文件解压后会被永久删除，请谨慎。\n分卷模式下只需要选择分卷索引.zip、.zip.001、part1文件\n解压分卷前，务必确认所有分卷完整)")
notice.pack()

# 创建运行按钮
run_state = tk.StringVar()
run_state.set(" 运行 ")
run_button = tk.Button(window, textvariable=run_state, command=run_program)
run_button.pack()

# 运行主循环
window.mainloop()