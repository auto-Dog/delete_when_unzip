# -*- coding: utf-8 -*-
# TODO: 设法完成分段zip的解压
import os
from stream_unzip import stream_unzip
import sys

def read_file_by_chunk(file_basepath,chunk_size=1024):
    '''按块读取文件，可指定块大小'''
    file_path,file_basename_zip = os.path.split(file_basepath)
    if file_path == '':
        file_path == './'
    file_basename,_ = os.path.splitext(file_basename_zip)
    file_list = []
    for root, dirs, files in os.walk(file_path):
        for file in files:
            if file.startswith(file_basename):
                file_list.append(os.path.join(root, file)) # 将按照z01,z02,...zip顺序排列
    for file in file_list:
        with open(file,'rb') as f: 
            _,file_ext = os.path.splitext(file) 
            if file_ext == '.z01':
                f.seek(4)   # .z01文件需要跳过头部4字节
            while True:
                chunk = f.read(chunk_size)
                pointer = f.tell()
                # print('Processing chunk at location {}'.format(pointer))    # debug
                if not chunk:
                    break
                yield chunk
        remove_one_chunk(file)  # 完成一块的解压，删除该块压缩文件
    return

def remove_one_chunk(file):
    '''删除已解压的分段压缩文件'''
    os.remove(file)


def main_unzip(file,chunk_size=1024):
    '''在本地流式解压文件，边解压边删除'''
    file_chunks = read_file_by_chunk(file,chunk_size)
    file_oripath,basename = os.path.split(file)
    file_folder = os.path.splitext(basename)[0]
    if not os.path.exists(os.path.join(file_oripath,file_folder)):
        os.makedirs(os.path.join(file_oripath,file_folder))
    i = 0
    for file_path_name, file_size, unzipped_chunks in stream_unzip(file_chunks):
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

