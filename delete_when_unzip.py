# -*- coding: utf-8 -*-
# TODO: 设法完成分段zip的解压
import os
from stream_unzip import stream_unzip
import sys

def shift_then_truncate(file,chunk_size=1024):
    '''将文件向头部平移chunksize，并保留未被覆盖的后半部分（相当于删除头部chunksize字节）'''
    with open(file,'rb+') as f: 
        pointer = chunk_size
        while True:
            f.seek(pointer)
            chunk = f.read(chunk_size)
            if not chunk:
                break
            new_pointer = f.tell()
            if new_pointer<=chunk_size: # 文件小于chunksize，不需要向头部移动
                break
            f.seek(pointer-chunk_size)
            f.write(chunk)  # 将第k段写入k-1段的空间内
            pointer = new_pointer   # 指向第k段末尾
            # print('shift once') # debug
        f.seek(pointer-chunk_size)  # 指向平移后的末尾
        f.truncate()

def read_file_by_chunk(file,chunk_size=1024):
    '''按块读取文件，可指定块大小'''
    while True:
        with open(file,'rb') as f: 
            f.seek(0)
            chunk = f.read(chunk_size)
            pointer = f.tell()
            if not chunk:
                return
            yield chunk
        shift_then_truncate(file,chunk_size)# [chunk_size:-1]的文件内容逐次向头部移动，相当于删除头部chunksize字节
        
def main_unzip(file,chunk_size=1024,password=None):
    '''在本地流式解压文件，边解压边删除'''
    chunk_size = int(chunk_size)    # python IO函数只支持int值参数
    file_chunks = read_file_by_chunk(file,chunk_size)
    file_oripath,basename = os.path.split(file)
    file_folder = os.path.splitext(basename)[0]
    if not os.path.exists(os.path.join(file_oripath,file_folder)):
        os.makedirs(os.path.join(file_oripath,file_folder))
    i = 0
    for file_path_name, file_size, unzipped_chunks in stream_unzip(file_chunks,password=password,chunk_size=chunk_size):
        # print('Processing chunk {}'.format(i))  # debug
        i+=1
        file_path_name = os.path.join(file_oripath,file_folder,file_path_name.decode('GBK'))
        dir_path,file_name = os.path.split(file_path_name)  # 检查文件存放路径的健全性
        # print(dir_path,file_name) # debug
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if file_name != "":
            with open(file_path_name,'wb+') as f:
                for chunk in unzipped_chunks:
                    f.write(chunk)
                f.close()
    os.remove(file)

if __name__ == '__main__':
    if len(sys.argv) <= 1 or len(sys.argv) >3:
        raise AttributeError('Wrong input param')
    if len(sys.argv) > 1:
        FILE_PATH = sys.argv[1]
        CHUNK_SIZE = 1024*1024*512.0  # 512MB per chunk
    if len(sys.argv) > 2:
        FILE_PATH = sys.argv[1]
        CHUNK_SIZE = eval(sys.argv[2])
    main_unzip(FILE_PATH,CHUNK_SIZE)
