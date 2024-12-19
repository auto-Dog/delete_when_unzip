# -*- coding: utf-8 -*-
# TODO: 测试可行性，以及加密后可行性
import os
import io
import re
from stream_unzip import stream_unzip
import sys
import libarchive as libap


file_list = []
def remove_one_chunk():
    '''删除已解压的分段压缩文件'''
    global file_list
    if len(file_list) == 0:
        return
    file = file_list.pop(0)
    print('Removing:{}'.format(file))   # debug
    os.remove(file)

def chain_streams(streams, buffer_size=io.DEFAULT_BUFFER_SIZE):
    """
    Chain an iterable of streams together into a single buffered stream.
    Usage:
    ```
        def generate_open_file_streams():
            for file in filenames:
                yield open(file, 'rb')
        f = chain_streams(generate_open_file_streams())
        f.read()
    ```
    _From: https://stackoverflow.com/questions/24528278/stream-multiple-files-into-a-readable-object-in-python_
    """

    class ChainStream(io.RawIOBase):
        def __init__(self):
            self.leftover = b''
            self.stream_iter = iter(streams)
            try:
                self.stream = next(self.stream_iter)
            except StopIteration:
                self.stream = None

        def readable(self):
            return True
        
        def seekable(self):
            return False

        def _read_next_chunk(self, max_length):
            # Return 0 or more bytes from the current stream, first returning all
            # leftover bytes. If the stream is closed returns b''
            if self.leftover:
                return self.leftover
            elif self.stream is not None:
                bytes_return = self.stream.read(max_length)
                return bytes_return
            else:
                return b''

        def readinto(self, b):
            buffer_length = len(b)
            chunk = self._read_next_chunk(buffer_length)
            while len(chunk) == 0:
                # move to next stream
                if self.stream is not None:
                    self.stream.close()
                try:
                    self.stream = next(self.stream_iter)
                    remove_one_chunk()
                    chunk = self._read_next_chunk(buffer_length)
                    # print(len(chunk))   # debug
                except StopIteration:
                    # No more streams to chain together
                    # print('############ Finish')    # debug
                    self.stream = None
                    b = b''
                    remove_one_chunk()
                    return 0  # indicate EOF
            output = chunk[:buffer_length]
            # print(len(chunk))   # debug
            b[:len(output)] = output
            return len(output)

    return io.BufferedReader(ChainStream(), buffer_size=buffer_size)

def unzip_buffer(e,file_root):
    ''' 解压一个buffer中的内容 '''
    
    for entry in e:
        rel_file_path = str(entry)    # 相对路径
        # print(entry.filetype,' ',rel_file_path)    # debug
        file_path_name = os.path.join(file_root,rel_file_path)
        if rel_file_path.endswith('/') or entry.filetype == 16384:   # 文件夹，不写入内容
            os.makedirs(file_path_name,exist_ok=True)
        else:
            file_multi_path,basename = os.path.split(file_path_name)
            os.makedirs(file_multi_path,exist_ok=True)
            with open(file_path_name, 'wb') as f1:  # 文件
                # for block in entry.get_blocks():
                #     f1.write(block)                
                try:
                    for block in entry.get_blocks():
                        f1.write(block)
                except:
                    print('>>>> Get blocks ERROR <<<<')

def generate_open_file_streams(filenames):
    ''' 将多个文件生成文件流迭代器 '''
    count = 1
    for file in filenames:
        with open(file,'rb+') as f:
            if len(filenames)>1 and file.endswith('.z01'):   # 多分卷
                f.seek(4)
            count+=1
            yield f

def main_unzip(file_path,chunk_size,password=None):
    '''在本地流式解压文件，边解压边删除. '''
    file_oripath,basename = os.path.split(file_path)
    file_folder = os.path.splitext(basename)[0]
    if file_folder.endswith('.zip') or file_folder.endswith('.ZIP'):    # 针对.zip.00x多重分段文件，不能让生成文件夹带后缀zip
        file_folder,_ = os.path.splitext(file_folder)
    if not os.path.exists(os.path.join(file_oripath,file_folder)):
        os.makedirs(os.path.join(file_oripath,file_folder))

    file_path,file_basename_zip = os.path.split(file_path)
    if file_path == '':
        file_path = './'
    file_basename,_ = os.path.splitext(file_basename_zip)
    if file_basename.endswith('.zip') or file_basename.endswith('.ZIP'):    # 针对.zip.00x多重分段文件
        file_basename,_ = os.path.splitext(file_basename)
    if file_basename.endswith('.part1') or file_basename.endswith('.part01'):    # 针对.part1.rar多重分段文件
        file_basename,_ = os.path.splitext(file_basename)
    global file_list
    file_list = []
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
    file_list.sort()    # 需按顺序读取
    # print(file_list)    # debug
    fs = chain_streams(generate_open_file_streams(file_list),chunk_size)
    # if password != None:
    #     password = password.encode()    # 存疑
    with libap.stream_reader(fs,passphrase=password) as e:
        unzip_buffer(e,os.path.join(file_oripath,file_folder))

if __name__ == '__main__':
    if len(sys.argv) <= 1 or len(sys.argv) >4:
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

# file_chunk_generator = read_file_by_chunk(file_path)
# for chunk in file_chunk_generator:
#     sys.stdout.write('UnRAR.exe x -si '+chunk.hex())

# with libap.file_reader(file_path) as ar:
#     unzip_buffer(ar)

# libap.extract_file(file_path)