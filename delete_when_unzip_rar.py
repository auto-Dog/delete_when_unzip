# -*- coding: utf-8 -*-
import os
import io
from stream_unzip import stream_unzip
import sys
import libarchive as libap

def shift_then_truncate(f,chunk_size=1024):
    '''将文件对象向头部平移chunksize，并保留未被覆盖的后半部分（相当于删除头部chunksize字节）'''
    # with open(file,'rb+') as f: 
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
    f.seek(0)

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
                global first_read_flag
                if first_read_flag:
                    first_read_flag=False
                else:
                    shift_then_truncate(self.stream,max_length)  # remove used bytes
                bytes_return = self.stream.read(max_length)
                # if len(bytes_return) != 0:
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
                    chunk = self._read_next_chunk(buffer_length)
                    # print(len(chunk))   # debug
                except StopIteration:
                    # No more streams to chain together
                    # print('############ Finish')    # debug
                    self.stream = None
                    b = b''
                    return 0  # indicate EOF
            output = chunk[:buffer_length]
            # print(len(chunk))   # debug
            b[:len(output)] = output
            return len(output)

    return io.BufferedReader(ChainStream(), buffer_size=buffer_size)

def unzip_buffer(e,file_root):
    ''' 将已经解压的buffer中的内容写入文件 '''
    
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
                for block in entry.get_blocks():
                    f1.write(block)
                # try:
                #     for block in entry.get_blocks():
                #         f1.write(block)
                # except:
                #     print('>>>> Get blocks ERROR <<<<')

def generate_open_file_streams(filenames):
    ''' 将多个文件生成文件流迭代器 '''
    count = 1
    for file in filenames:
        with open(file,'rb+') as f:
            # if len(filenames)>1 and count==1:   # 多分卷
            #     f.seek(4)
            count+=1
            yield f
            f.close()

def main_unzip(file_path,chunk_size,password=None):
    '''在本地流式解压文件，边解压边删除. '''
    file_oripath,basename = os.path.split(file_path)
    file_folder = os.path.splitext(basename)[0]
    if not os.path.exists(os.path.join(file_oripath,file_folder)):
        os.makedirs(os.path.join(file_oripath,file_folder))
    global first_read_flag
    first_read_flag = True 
    fp = open(file_path,'rb+')
    try:
        fs = chain_streams([fp],chunk_size)
        # if password != None:
        #     password = password.encode()    # 存疑
        with libap.stream_reader(fs,passphrase=password) as e:
            unzip_buffer(e,os.path.join(file_oripath,file_folder))
        fp.close()
        if not first_read_flag:
            os.remove(file_path)
    except Exception as err:
        fp.close()
        raise err

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