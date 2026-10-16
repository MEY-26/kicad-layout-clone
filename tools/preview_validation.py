"""Dependency-free checks for externally captured documentation PNGs.

These checks reject the transparent wx ClientDC captures that previously reached
GitHub. They are a publication guard, not a substitute for viewing the actual
README in light and dark themes. No screen or application APIs are used here.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import struct
import zlib


def _paeth(left, up, upper_left):
    prediction = left + up - upper_left
    distances = (abs(prediction-left), abs(prediction-up), abs(prediction-upper_left))
    return (left, up, upper_left)[distances.index(min(distances))]


def _pixels(data):
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Preview must be a PNG file')
    offset, header, compressed, ended = 8, None, bytearray(), False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated PNG chunk')
        length = struct.unpack_from('>I', data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('Truncated PNG data')
        kind = data[offset+4:offset+8]
        payload = data[offset+8:offset+8+length]
        crc = struct.unpack_from('>I', data, offset+8+length)[0]
        if zlib.crc32(kind+payload) & 0xffffffff != crc:
            raise ValueError('PNG checksum mismatch')
        if kind == b'IHDR':
            if header is not None or length != 13:
                raise ValueError('Invalid PNG header')
            header = struct.unpack('>IIBBBBB', payload)
        elif kind == b'IDAT':
            compressed.extend(payload)
        elif kind == b'IEND':
            ended = True
            break
        elif kind == b'tRNS':
            raise ValueError('Preview must not contain PNG transparency')
        offset = end
    if not header or not ended:
        raise ValueError('Incomplete PNG')
    width, height, depth, color_type, compression, filtering, interlace = header
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type)
    if depth != 8 or channels is None or compression or filtering or interlace:
        raise ValueError('Use a non-interlaced 8-bit RGB/RGBA PNG capture')
    if not width or not height or width*height > 32_000_000:
        raise ValueError('Invalid or oversized preview dimensions')
    stride = width*channels
    expected = (stride+1)*height
    try:
        inflater = zlib.decompressobj()
        raw = inflater.decompress(bytes(compressed), expected+1)
    except zlib.error as error:
        raise ValueError('Invalid compressed PNG data') from error
    if len(raw) != expected or not inflater.eof or inflater.unconsumed_tail:
        raise ValueError('PNG pixel data has an invalid length')
    previous = bytearray(stride)
    for start in range(0, len(raw), stride+1):
        filter_type = raw[start]
        row = bytearray(raw[start+1:start+1+stride])
        if filter_type == 1:
            for index in range(channels, stride):
                row[index] = (row[index]+row[index-channels]) & 255
        elif filter_type == 2:
            for index in range(stride):
                row[index] = (row[index]+previous[index]) & 255
        elif filter_type in (3, 4):
            for index in range(stride):
                left = row[index-channels] if index >= channels else 0
                upper_left = previous[index-channels] if index >= channels else 0
                predictor = ((left+previous[index])//2 if filter_type == 3
                             else _paeth(left, previous[index], upper_left))
                row[index] = (row[index]+predictor) & 255
        elif filter_type != 0:
            raise ValueError('Unknown PNG row filter')
        yield width, height, color_type, channels, row
        previous = row


def validate_preview(path, minimum_size=(640, 400)):
    """Return an asset report, or raise ValueError for unsafe/blank preview data.

    Fully opaque RGB and RGBA screenshots are accepted. Alpha flattening is not
    performed: it cannot restore missing native controls, so a bad capture must
    be recaptured instead. Only near-uniform images are rejected by the basic
    content check; text legibility still requires a real visual review.
    """
    path = Path(path)
    data = path.read_bytes()
    if len(data) > 40_000_000:
        raise ValueError('Preview PNG is unexpectedly large')
    colors, nonopaque, width, height = Counter(), 0, 0, 0
    for width, height, color_type, channels, row in _pixels(data):
        if width < minimum_size[0] or height < minimum_size[1]:
            raise ValueError('Preview resolution is too small for readable documentation')
        if color_type in (4, 6):
            nonopaque += sum(alpha != 255 for alpha in row[channels-1::channels])
        # A coarse histogram is sufficient to detect accidentally blank windows.
        # Sample every fourth pixel to keep multi-megapixel captures inexpensive.
        for index in range(0, len(row), channels*4):
            rgb = row[index:index+3] if channels >= 3 else row[index:index+1]*3
            colors[tuple(value//16 for value in rgb)] += 1
    if nonopaque:
        raise ValueError(f'Preview contains {nonopaque} non-opaque pixels; recapture the real window')
    dominant_fraction = max(colors.values()) / sum(colors.values())
    if dominant_fraction > .985:
        raise ValueError('Preview is overwhelmingly blank; inspect and recapture the real window')
    return {'width': width, 'height': height, 'nonopaque_pixels': nonopaque,
            'dominant_color_fraction': round(dominant_fraction, 6),
            'sha256': hashlib.sha256(data).hexdigest()}


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('images', type=Path, nargs='+')
    args = parser.parse_args()
    for image in args.images:
        try:
            print(json.dumps({'file': str(image), **validate_preview(image)}))
        except (OSError, ValueError) as error:
            parser.exit(1, f'{image}: {error}\n')
