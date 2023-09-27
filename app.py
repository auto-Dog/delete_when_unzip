import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import subprocess
from delete_when_unzip import main_unzip as single_unzip
from delete_when_unzip_multi import main_unzip as multi_unzip


def run_program():
    run_button['state'] = 'disable'
    file_path = file_entry.get()
    number = number_entry.get()
    number = eval(number)*1024*1024
    # number = str(number)
    mode = var_mode.get()

    if checkbox_var.get() == 1:
        password_str = password_entry.get()
    else:
        password_str = None
    try:
        # 运行命令行程序
        if mode == 'mode1':
            single_unzip(file_path,number,password_str)
            # result = subprocess.run(['python', './delete_when_unzip.py', file_path, number], capture_output=True, text=True)
        elif mode == 'mode2':
            multi_unzip(file_path,number,password_str)
        #     result = subprocess.run(['python', './delete_when_unzip_multi.py', file_path, number], capture_output=True, text=True)
        # output = result.stdout
        # outerr = result.stderr
        # if outerr:
        #     raise RuntimeError(outerr)
        messagebox.showinfo("Successfully Unzipped!","Successfully Unzipped!")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    run_button['state'] = 'normal'

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
var_mode.set("mode2")

# 创建运行按钮
run_button = tk.Button(window, text="运行", command=run_program)
run_button.pack()

# 运行主循环
window.mainloop()