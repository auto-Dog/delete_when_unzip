# Delete When Unzip ——边解压边删除的解压工具
---
## Usage
```bash
pip install -r requirements.txt
```

```bash
python delete_when_unzip.py filepath chunk_size(byte) password(optional)   # 1 zip file, support zip
python delete_when_unzip_rar.py filepath chunk_size(byte) password(optional)   # 1 zip file, support rar, etc.

# when unzip segmented ones (multi-volume archives)
python delete_when_unzip_multi.py filepath(name of the main volume, *.zip) chunk_size(byte) password(optional)   # segmented zip files,  support zip
python delete_when_unzip_rar_multi.py filepath(name of the main volume, *.zip) chunk_size(byte) password(optional) # segmented zip files, support rar, etc.
```
Visualize interface:
```bash
python app.py
```

---
_对于大型游戏压缩文件解压需要翻倍空间的情况，这是一个值得拥有的工具. 可以边解压便删除完成部分_  
_GOODNEWS FOR GAMERS! Big ZIP/RAR files can be unzipped under limited disk space，no need for doubled space. It deletes used parts when uncompressing archive._ 

* 通常，下载并解压100G的游戏压缩文件需要至少200G的空间，对硬盘空间有限的用户及其不友好
* Usually, a 100G game requires at least 200G disk space when download and unzip, which is bad for users with limited space  

* 本工具利用流式解压库`stream_unzip`，将本地压缩文件按顺序流式读取到内存，每次读取固定大小的块并解压。在解压过一部分块后，立即删除原压缩文件的块，因此解压过程中对硬盘的占用将远远小于压缩文件的2倍。NEW: 使用libarchive库，自行构建了文件流读取器，支持zip，rar，tar等。利用unrar cli工具可以高效解压并删除分卷rar（windows下可用）

* The program imports `stream_unzip` and sees local ZIP file as a stream. For each iteration it reads a chunk into memory then apply unzip algorithm. After 'unzip a chunk', it deteles the in original ZIP file, thus keeps a low usage of disk space(at least you donnot need doubled space to unzip) NEW: use libarchive library with custome file streamer. Now support zip，rar，tar.gz files. For Windows User a unrar CLI interface is efficiently used for rar volumes。

  
  
* 支持单文件和**分段zip,RAR文件**(大多游戏资源文件形式，如原神)边解压边删除。当前支持zip,rar类型文件

* Support both single zip and segmented zip/RAR, both can be deleted when unzip. RAR is also supported now!

* 注意：边解边删有中途解压失败的风险，失败可能导致压缩包损坏
* ATTENTION: If error occurs when unzip&delete, the archive might be damaged.