# -*- coding: utf-8 -*-
# TODO: 设法完成分段zip的解压
import os
from stream_unzip import stream_unzip
import sys

def shift_then_truncate(file,chunk_size=1024):
    '''将文件向头部平移chunksize，并保留未被覆盖的后半部分'''
    with open(file,'rb+') as f: 
        pointer = chunk_size
        while True:
            f.seek(pointer)
            chunk = f.read(chunk_size)
            if not chunk:
                break
            new_pointer = f.tell()
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
        shift_then_truncate(file,chunk_size)# [chunk_size:-1]的文件内容逐次向左移动，最后截断只保留这部分内容
        yield chunk
# def remove_one_chunk(file,chunk_size=1024):
#     '''删除文件头部若干长度的内容'''
#     f_size = os.path.getsize(file)
#     # print(f_size)
#     with open(file,'rb+') as f:
#         if f_size<chunk_size:
#             chunk_size = f_size
#         f.seek(chunk_size)
#         f.truncate(f_size-chunk_size)
#         f.seek(0)
#     print('Removed {:.2f} MB'.format(chunk_size/1024/1024))

def main_unzip(file,chunk_size=1024):
    '''在本地流式解压文件，边解压边删除'''
    file_chunks = read_file_by_chunk(file,chunk_size)
    i = 0
    for file_path_name, file_size, unzipped_chunks in stream_unzip(file_chunks,chunk_size=chunk_size):
        # print('Processing chunk {}'.format(i))  # debug
        i+=1
        file_path_name = os.path.join('./test_folder/',file_path_name.decode('GBK'))
        dir_path,file_name = os.path.split(file_path_name)  # 检查文件存放路径的健全性
        # print(dir_path,file_name) # debug
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if file_name != "":
            with open(file_path_name,'wb+') as f:
                for chunk in unzipped_chunks:
                    f.write(chunk)
                f.close()

if __name__ == '__main__':
    if len(sys.argv) <= 1 or len(sys.argv) >3:
        raise AttributeError('Wrong input param')
    if len(sys.argv) > 1:
        FILE_PATH = sys.argv[1]
        CHUNK_SIZE = 1024*1024*512  # 512MB per chunk
    if len(sys.argv) > 2:
        FILE_PATH = sys.argv[1]
        CHUNK_SIZE = eval(sys.argv[2])
    main_unzip(FILE_PATH,CHUNK_SIZE)
    os.remove(FILE_PATH)
