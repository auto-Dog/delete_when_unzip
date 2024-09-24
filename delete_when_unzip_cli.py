import subprocess
import re
import os
import sys

file_list = []
def remove_one_chunk():
    '''删除已解压的分段压缩文件'''
    global file_list
    if len(file_list) == 0:
        return
    file = file_list.pop(0)
    if file == 'HEAD':  # 第一次调用，不删除文件，等待下一次调用
        return
    # print('Removing:{}'.format(file))   # debug
    os.remove(file)

def run_and_monitor_command(command):
    '''子进程启动外部程序'''
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    # 实时监听程序的输出
    try:
        while True:
            # 读取一行输出
            line = process.stdout.readline()
            if not line:
                break
            # print(line, end='')  # 打印所有输出
            # 检查是否包含 "Extracting from"
            if "Extracting from" in line:
                # print(f"Found 'Extracting from' in the output: {line.strip()}")# debug
                try:
                    remove_one_chunk()
                except Exception as e_rm:
                    print(f"Can NOT remove one chunk: {e_rm}")
            if "All OK" in line:
                # print("Finished")   # debug
                remove_one_chunk()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 等待程序结束
        process.communicate()

def main_unzip(file_path,chunk_size=0,password=None):
    '''在本地流式解压文件，边解压边删除. '''
    file_oripath,basename = os.path.split(file_path)
    file_folder = os.path.splitext(basename)[0]
    # if file_folder.endswith('.zip') or file_folder.endswith('.ZIP'):    # 针对.zip.00x多重分段文件，不能让生成文件夹带后缀zip
    #     file_folder,_ = os.path.splitext(file_folder)
    if not os.path.exists(os.path.join(file_oripath,file_folder)):
        os.makedirs(os.path.join(file_oripath,file_folder))

    dir_path,file_basename_zip = os.path.split(file_path)
    if dir_path == '':
        dir_path = './'
    file_basename,_ = os.path.splitext(file_basename_zip)
    # if file_basename.endswith('.zip') or file_basename.endswith('.ZIP'):    # 针对.zip.00x多重分段文件
    #     file_basename,_ = os.path.splitext(file_basename)
    if file_basename.endswith('.part1'):    # 针对.part1.rar多重分段文件
        file_basename,_ = os.path.splitext(file_basename)
    global file_list
    file_list = []
    files = os.listdir(dir_path)
    # 筛出file_basename.rar, file_basename.r01, file_basename.part1.rar ...
    pattern1 = re.compile(rf"{re.escape(file_basename)}\.z\d+",re.I)
    pattern2 = re.compile(rf"{re.escape(file_basename)}\.zip",re.I)
    pattern3 = re.compile(rf"{re.escape(file_basename)}\.zip\.\d+",re.I)
    pattern4 = re.compile(rf"{re.escape(file_basename)}\.r\d+",re.I)
    pattern5 = re.compile(rf"{re.escape(file_basename)}\.rar",re.I)
    pattern6 = re.compile(rf"{re.escape(file_basename)}\.rar\.\d+",re.I)
    pattern7 = re.compile(rf"{re.escape(file_basename)}\.part\d+\.rar",re.I)
    for file in files:
        if pattern4.match(file) or pattern5.match(file) or pattern6.match(file) or pattern7.match(file):
        # if file.startswith(file_basename) and os.path.isfile(os.path.join(dir_path, file)):
            file_list.append(os.path.join(dir_path, file)) # 将按照part1,part2,...顺序排列
    file_list.sort()    # 需按顺序读取
    file_list = ['HEAD']+file_list
    # print(file_list)    # debug
    # 使用示例
    # 请替换下面的 'name.exe -option1 xxx' 为你想要执行的命令
    command_to_run = ['unrar.exe', 'x','-o+', file_path,os.path.join(file_oripath,file_folder)]
    if password != None:
        command_to_run = ['unrar.exe', 'x','-p'+password,'-o+', file_path,os.path.join(file_oripath,file_folder)]
    run_and_monitor_command(command_to_run)

if __name__ == '__main__':
    if len(sys.argv) <= 1 or len(sys.argv) >3:
        raise AttributeError('Wrong input param')
    password = None
    if len(sys.argv) > 1:
        FILE_PATH = sys.argv[1]
        CHUNK_SIZE = 1024*1024*512.0  # 512MB per chunk
    if len(sys.argv) > 2:
        FILE_PATH = sys.argv[1]
        CHUNK_SIZE = eval(sys.argv[2])
    if len(sys.argv) > 3:
        FILE_PATH = sys.argv[1]
        CHUNK_SIZE = eval(sys.argv[2])
        password = sys.argv[3]
    CHUNK_SIZE = 10_240_000
    main_unzip(FILE_PATH,CHUNK_SIZE,password)
