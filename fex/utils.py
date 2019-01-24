from binascii import crc32
from hashlib import sha1


def convert_size(size, precision=2):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffix_index = 0
    while size > 1024 and suffix_index < 4:
        suffix_index += 1
        size = size / 1024.0
    return '%.*f%s' % (precision, size, suffixes[suffix_index])


def calculate_sha1(file):
    sha1sum = sha1()
    with open(file, 'rb') as f:
        block = f.read(2 ** 16)
        while len(block) != 0:
            sha1sum.update(block)
            block = f.read(2 ** 16)
    return sha1sum.hexdigest()


def calculate_crc32(file):
    buf = open(file, 'rb').read()
    buf = (crc32(buf) & 0xFFFFFFFF)
    buf = '%08X' % buf
    return buf.lower()
