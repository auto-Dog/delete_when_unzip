---
name: delete-when-unzip
description: Use when the user wants to extract/unpack large ZIP or RAR archives while disk space is limited, or mentions "delete when unzip", "边解压边删除", "extract and delete processed parts", "flat/unpack files", or segmented (multi-volume) archives (.z01/.zip.001/.part1.rar/.r01) under low free space. This project streams archives chunk by chunk and deletes already-processed parts so you do not need 2x the archive size in free space. Covers which script to run, chunk-size math, and the critical warning that the source archive is destroyed.
---

# Delete When Unzip — 边解压边删除的解压工具

Stream-extract a local archive **chunk by chunk, deleting each processed part of the original archive** as you go. For example, a 100 GB game archive can be extracted with roughly **100 GB + 1 chunk** of free space instead of 200 GB. Source files live in this repo.

## What the user is asking for

The core scenario this skill serves:
1. Disk space is limited (insufficient to hold both the full archive and its extracted contents).
2. The user wants the archive's files extracted/unpacked ("flatten files" / 解压) **and** the already-processed parts of the archive deleted as extraction proceeds.
3. The archive is usually a large game: single ZIP/RAR or multi-volume (分卷) sets.

> **"Flatten" caveat:** extraction preserves the archive's *internal* directory structure — there is **no option to extract flat (all files into one directory)**. Output goes into a folder named after the archive's base name. If the user asks to truly flatten output, that is a missing feature, not a usage flag; say so and offer to add it.

## Script map (which one to run)

| Script | Archive type | Engine | Deletion strategy |
|---|---|---|---|
| `delete_when_unzip.py` | single **ZIP** | `stream_unzip` | `shift_then_truncate()` shrinks the archive in place as chunks are consumed; `os.remove()` at the end |
| `delete_when_unzip_rar.py` | single **RAR / ZIP / TAR / TAR.GZ** (libarchive-supported) | `libarchive.stream_reader` over a custom `chain_streams` reader | same in-place shrink via `shift_then_truncate()` |
| `delete_when_unzip_multi.py` | segmented **ZIP** (`.z01 .z02 .zip`, `.zip.001`) | `stream_unzip` | each volume is deleted (`os.remove`) after it has been fully streamed — volumes are **not** truncated in place |
| `delete_when_unzip_cli.py` | segmented **RAR** (`.part1.rar .part01.rar .r01 .rar`, `.rar.001`) | `unrar.exe` subprocess, output monitored | deletes a volume as soon as unrar prints `Extracting from` the next one; final volume deleted on `All OK` — **recommended on Windows** |
| `delete_when_unzip_rar_multi.py` | segmented anything else via libarchive | `libarchive.stream_reader` | volume deleted when the chain advances to the next one |
| `app.py` | — (GUI wrapping all of the above) | Tkinter | 6 modes, chunk size in **MB** |
| `robust_split.py` | helper | — | `robust_basename_split()` strips volume markers to find the base name |
| `boosting/` | libarchive-c weak-decryption (zipcrypto) | — | build artifacts — do not modify |

### Decision flow
1. **Single file?**
   - `.zip` → `delete_when_unzip.py`
   - `.rar` or any other libarchive format (tar, tar.gz) → `delete_when_unzip_rar.py`
2. **Multi-volume (分卷)?** User should point at the **main volume** (e.g. `xxx.zip`, `xxx.zip.001`, `xxx.part1.rar`), not the last part.
   - `.zip.001` / `.z01` → `delete_when_unzip_multi.py`
   - `.part1.rar` / `.part01.rar` / `.r01` → `delete_when_unzip_cli.py` (unrar, **recommended** on Windows)
       Note: The unrar CLI utility is Windows-oriented x64; if the system platform is not Windows x64, unrar.exe might require a redownload from [https://www.rarlab.com/download.htm](https://www.rarlab.com/download.htm).
   - other segmented formats → `delete_when_unzip_rar_multi.py`


## CLI usage

```bash
# single archives
python delete_when_unzip.py <archive_path> [chunk_size_bytes] [password]        # ZIP
python delete_when_unzip_rar.py <archive_path> [chunk_size_bytes] [password]     # RAR/other via libarchive

# segmented (multi-volume) archives — point at the MAIN volume
python delete_when_unzip_multi.py <main_volume> [chunk_size_bytes] [password]    # segmented ZIP
python delete_when_unzip_cli.py <main_volume> [chunk_size_bytes] [password]      # segmented RAR (unrar)
python delete_when_unzip_rar_multi.py <main_volume> [chunk_size_bytes] [password]# segmented other (libarchive)
```

- Default chunk size: 512 MB. Provide it in **bytes** (e.g. `10485760` for 10 MB). Decide the chunk size based on the remained memory space. The bigger the chunk size, the faster the extraction speed and more memory is required. 
- **Gotcha:** `delete_when_unzip_rar.py`, `delete_when_unzip_rar_multi.py`, and `delete_when_unzip_cli.py` **hardcode `CHUNK_SIZE = 10_240_000` (~10 MB) at the bottom of `__main__`, overriding the argument**. Only `delete_when_unzip.py` and `delete_when_unzip_multi.py` actually honor `sys.argv[2]`. So when the user wants a small chunk on a very tight disk, prefer the ZIP (`_unzip.py`) paths or the GUI, or edit the hardcoded value.
- `chunk_size` is parsed with `eval()` — supports arithmetic, but be aware it is arbitrary code execution in the CLI arg.
- Password is optional, passed as a plain string.

## Output behavior

- Output folder is created **next to the archive**, named after the volume-set base name (via `robust_basename_split`). E.g. `game.7z.001` → folder `game/`; `game.part1.rar` → `game/`.
- Internal directory structure of the archive is preserved.
- `stream_unzip`-based scripts decode member filenames as **GBK** (`file_path_name.decode('GBK')`) — archives with non-GBK names may fail there. The libarchive paths handle names via `str(entry)`.

## Disk-space model (explain this to the user)

- **Single-file scripts:** the archive shrinks in place as chunks are consumed (`shift_then_truncate` rewrites the remainder toward the front and truncates). Peak extra space ≈ size of the output written so far + ~1 chunk of the archive. The archive file still occupies its (shrinking) size until the end, then is `os.remove()`'d.
- **Multi-volume scripts:** each whole volume is deleted as it is consumed (or when unrar moves to the next), so peak = remaining volumes + output. Savings are coarser (per-volume) than the single-file in-place shrink.
- **Trade-off:** a smaller chunk = less peak temporary space but more shift/truncate overhead; on huge archives `shift_then_truncate` is O(n²)-ish. For a very tight disk, recommend a small chunk (e.g. 10–50 MB) on the ZIP path.
- The `.z01` first volume has a 4-byte header that is skipped via `seek(4)` — handled automatically by `delete_when_unzip_multi.py`.

## ⚠️ CRITICAL: the source archive is destroyed

- After a successful extraction, the original archive is **deleted** (`os.remove`) or truncated down until it disappears. There is no "keep the archive" mode.
- If extraction fails/interrupts midway, the archive is left **damaged/partial** and the output is incomplete.
- **Always warn the user before running:** if the archive is their only copy, tell them to back it up first. This is the single most important thing to communicate.

## Troubleshooting (from the GUI's error map + code)

| Symptom | Meaning / fix |
|---|---|
| `'7z'` or `UnsupportedCompressionTypeError(14)` | unsupported compression algorithm — use a different path |
| `'Rar!'` in the error | must run in RAR mode — pick `delete_when_unzip_rar.py`/CLI |
| `Decryption is unsupported` / `Unsupported block header size` | libarchive **cannot decrypt an encrypted single RAR** — use the unrar CLI path instead |
| `'str' object cannot be interpreted as an integer` | wrong mode selected for the file — switch single↔volumes |
| `unrar.exe` / `./unrar.exe` not found | `delete_when_unzip_cli.py` invokes `./unrar.exe` relative to cwd — **run from the repo dir**, or get the right unrar for the platform from rarlab.com |
| huge archive, very slow | it is the O(n²) `shift_then_truncate` with small chunks on a giant file — accept the wait or use the unrar CLI path |

Platform notes: the unrar CLI path is Windows-oriented (bundled `unrar.exe`); the libarchive path is cross-platform but may need the compiled `boosting/` weak-decrypt module for encrypted zips. GUI chunk size is entered in **MB**.

## What to actually do when invoked

1. Confirm what the archive is (single vs. multi-volume, format) and how much free disk space there is.
2. Pick the script from the map above; build the command with the archive path (main volume for segmented sets) and a chunk size that leaves clear headroom.
3. **State the destruction risk** before running — offer to back up if the archive is the only copy.
4. Run from the repo directory so `unrar.exe` resolves, then verify the output folder was created and the archive(s) are gone.

## Other Rules
1. Answer user in the language they used to ask the question.
2. List the files that will be processed before running the script, and confirm with the user that they want to proceed.
3. Try to uncomment all #debug sentences so that you can monitor the process during unzip. Once an error occurs, stop the delete when unzip process to avoid delete!