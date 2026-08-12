# Delete When Unzip

---
## Usage
Install: 
```bash
pip install -r requirements.txt
```

Install as Agent Skill (for Codex, CC, etc.):
```text
Install the skill from https://github.com/auto-Dog/delete_when_unzip.git and read `skill.md`.
```

### When unzip single archive files:
Single archived file, for `.zip` format:
```bash
python delete_when_unzip.py filepath chunk_size(byte) password(optional)
```
Single archived file, for `.rar` format:
```bash
python delete_when_unzip_rar.py filepath chunk_size(byte) password(optional)
```

### When unzip segmented ones (multi-volume archives)
Segmented rar files, for `.zip.001`, `.z01` format:
```bash
python delete_when_unzip_cli.py filepath(name of the main volume) chunk_size(byte) password(optional)
```

Segmented rar files, for `.rar.001`, `.part1.rar` format:
```bash
python delete_when_unzip_rar_multi.py filepath(name of the main volume) chunk_size(byte) password(optional)
```

Segmented rar files, for `.rar.001`, `.part1.rar` format **(Recommand)**:

```bash
python delete_when_unzip_cli.py filepath(name of the main volume) chunk_size(byte) password(optional)
```
Note: This version uses `unrar.exe` and monitor cli progress, for windows x64. If you are using other systems, find your suitable version at [https://www.rarlab.com/download.htm](https://www.rarlab.com/download.htm).

Visualize interface:
```bash
python app.py
```

---

_对于大型游戏压缩文件解压需要翻倍磁盘空间的情况，这是一个值得拥有的工具。该工具可以边解压边删除已完成解压的部分，因此无须空间翻倍。_  
_GOOD NEWS FOR GAMERS! Large ZIP/RAR archives can be extracted with limited disk space—no need for double the space. The tool deletes processed parts while extracting, so you don’t need extra room to keep both the full archive and the extracted files._

- 通常，下载并解压 100G 的游戏压缩文件需要至少 200G 的空间，这对硬盘空间有限的用户非常不友好  
- Usually, downloading and extracting a 100G game archive requires at least 200G of disk space, which is painful for users with limited storage.

- 本工具利用流式解压库 `stream_unzip`，将本地压缩文件按顺序以流的形式读取到内存：每次读取固定大小的块并解压；当某部分内容解压完成后，立即删除原压缩文件中已处理的块，从而显著降低解压过程中的磁盘占用。  
  NEW：使用 libarchive 库并实现自定义文件流读取器，支持 zip、rar、tar 等格式；在 Windows 上可通过 unrar CLI 高效解压并删除分卷 rar。  

- This tool uses the streaming extraction library `stream_unzip` and treats a local archive as a stream: it reads fixed-size chunks into memory and extracts them; after a chunk is processed, the corresponding part of the original archive is deleted to keep disk usage low (i.e., you don’t need double the space).  
  NEW: A custom file streamer based on libarchive is included, supporting ZIP, RAR, TAR, etc. On Windows, an unrar CLI interface can be used to efficiently extract and delete multi-volume RAR archives.

- 支持单文件与**分段 zip / RAR 文件**（常见于大型游戏资源，如原神）边解压边删除；当前支持 zip、rar 等格式  
- Supports both single archives and **segmented ZIP/RAR** archives. Deleting during extraction is supported, and RAR is supported as well.

- 注意：边解压边删除存在中途解压失败的风险，失败可能导致压缩包损坏  
- ATTENTION: If an error occurs during _extract & delete_, the archive may be damaged.

## Star History

<a href="https://www.star-history.com/?repos=auto-Dog%2Fdelete_when_unzip&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=auto-Dog/delete_when_unzip&type=date&theme=dark&legend=top-left&sealed_token=xdwL7FsYDLXc-LJ6F9EsMUPtLbfUeOI0CctBsOZwrGr-tSgCxUl6du2tqNrFweG5PRv9-FChsG385agEqZtnpNvqWMqOaG6SBgOuG5Ud9QWNjy7T9Me9gw" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=auto-Dog/delete_when_unzip&type=date&legend=top-left&sealed_token=xdwL7FsYDLXc-LJ6F9EsMUPtLbfUeOI0CctBsOZwrGr-tSgCxUl6du2tqNrFweG5PRv9-FChsG385agEqZtnpNvqWMqOaG6SBgOuG5Ud9QWNjy7T9Me9gw" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=auto-Dog/delete_when_unzip&type=date&legend=top-left&sealed_token=xdwL7FsYDLXc-LJ6F9EsMUPtLbfUeOI0CctBsOZwrGr-tSgCxUl6du2tqNrFweG5PRv9-FChsG385agEqZtnpNvqWMqOaG6SBgOuG5Ud9QWNjy7T9Me9gw" />
 </picture>
</a>
