#cython:language_level=3
import zlib

class weak_decrypt:
    def __init__(self) -> None:
        self.key_0 = 305419896
        self.key_1 = 591751049
        self.key_2 = 878082192
        self.crc32 = zlib.crc32
        self.bytes_c = bytes

    def update_keys(self,char byte):
        self.key_0 = ~self.crc32(self.bytes_c((byte,)), ~self.key_0) & 0xFFFFFFFF
        self.key_1 = (self.key_1 + (self.key_0 & 0xFF)) & 0xFFFFFFFF
        self.key_1 = ((self.key_1 * 134775813) + 1) & 0xFFFFFFFF
        self.key_2 = ~self.crc32(self.bytes_c((self.key_1 >> 24,)), ~self.key_2) & 0xFFFFFFFF

    def decrypt(self,chunk):
        chunk = bytearray(chunk)
        cdef char byte
        cdef int i
        cdef int temp
        for i, byte in enumerate(chunk):
            temp = self.key_2 | 2
            byte ^= ((temp * (temp ^ 1)) >> 8) & 0xFF
            self.update_keys(byte)
            chunk[i] = byte
        return bytes(chunk)