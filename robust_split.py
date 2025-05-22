import re

def robust_basename_split(basename_with_ext):
    '''给定一个文件名，处理各种分卷文件名模式，提取基础名。对于非压缩文件，返回全名'''
    # 支持 .zip, .zip.001, .rar, .part1.rar, .part01.rar, .zip.z01, .zip.001, .rar.001, .rar.part01, .zip.002, .zip.003, .rar.002, .rar.003, .zip.7z.001 等
    # 例如 file_basename: abc.part1, abc.part01, abc.z01, abc.001, abc, abc.part1.rar, abc.part01.rar, abc.rar, abc.zip, abc.zip.001, abc.zip.z01
    # 统一去除 .partN, .zNN, .zip, .rar, .001, .002, .003, .7z.001, .tar.gz, .tar, .gz, .ZIP, .RAR, .ZNN, .ZIP.001, .ZIP.Z01, .RAR.001, .RAR.PART01
    # 只保留最基础的文件名
    base = basename_with_ext
    # 去除多重后缀
    patterns = [
        r'(.*)\.part\d+$',           # abc.part1, abc.part01
        r'(.*)\.z\d+$',              # abc.z01, abc.z02
        r'(.*)\.r\d+$',              # abc.r01, abc.r02
        r'(.*)\.zip$',               # abc.zip
        r'(.*)\.rar$',               # abc.rar
        r'(.*)\.\d+$',               # abc.001, abc.002
        r'(.*)\.tar\.gz$',           # abc.tar.gz
        r'(.*)\.tar$',               # abc.tar
        r'(.*)\.gz$',                # abc.gz
        r'(.*)\.ZIP\.\d+$',          # abc.ZIP.001
        r'(.*)\.ZIP\.Z\d+$',         # abc.ZIP.Z01
        r'(.*)\.RAR\.\d+$',          # abc.RAR.001
        r'(.*)\.RAR\.PART\d+$',      # abc.RAR.PART01
        r'(.*)\.PART\d+.RAR$',      # abc.PART01.RAR
        r'(.*)\.7z\.\d+$',           # abc.7z.001
    ]
    base_out = base
    for pat in patterns:
        m = re.match(pat, base, re.I)
        if m:
            base_out = m.group(1)
    return base_out