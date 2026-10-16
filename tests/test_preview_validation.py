"""Publication asset checks use generated PNG bytes, never screen captures."""
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from preview_validation import _paeth, validate_preview


def chunk(kind, data):
    return (struct.pack('>I', len(data))+kind+data+
            struct.pack('>I', zlib.crc32(kind+data) & 0xffffffff))


def png(*, alpha=True, transparent=False, blank=False, filter_type=0):
    width, height, channels = 32, 24, 4 if alpha else 3
    previous, rows = bytearray(width*channels), bytearray()
    for y in range(height):
        row = bytearray()
        for x in range(width):
            row.extend((240, 240, 240) if blank else (x*7, y*9, (x+y)*4))
            if alpha:
                row.append(0 if transparent and x == 15 and y == 12 else 255)
        encoded = bytearray()
        for index, value in enumerate(row):
            left = row[index-channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index-channels] if index >= channels else 0
            predictors = (0, left, up, (left+up)//2, _paeth(left, up, upper_left))
            encoded.append((value-predictors[filter_type]) & 255)
        rows.extend(bytes([filter_type])+encoded)
        previous = row
    header = struct.pack('>IIBBBBB', width, height, 8, 6 if alpha else 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', header)+chunk(b'IDAT', zlib.compress(rows))+chunk(b'IEND', b'')


class PreviewValidationTests(unittest.TestCase):
    def validate(self, data, minimum_size=(1, 1)):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'capture.png'
            path.write_bytes(data)
            return validate_preview(path, minimum_size)

    def test_all_png_filters_decode_opaque_rgb_and_rgba(self):
        for alpha in (False, True):
            for filter_type in range(5):
                with self.subTest(alpha=alpha, filter=filter_type):
                    report = self.validate(png(alpha=alpha, filter_type=filter_type))
                    self.assertEqual((report['width'], report['height']), (32, 24))
                    self.assertEqual(report['nonopaque_pixels'], 0)

    def test_even_one_transparent_pixel_is_rejected(self):
        for filter_type in range(5):
            with self.subTest(filter=filter_type), self.assertRaisesRegex(ValueError, 'non-opaque'):
                self.validate(png(transparent=True, filter_type=filter_type))

    def test_blank_opaque_capture_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'blank'):
            self.validate(png(blank=True))

    def test_truncated_and_corrupt_captures_are_rejected(self):
        for data in (png()[:-9], b'not a PNG', png()[:-1]+b'!'):
            with self.assertRaises(ValueError):
                self.validate(data)

    def test_unreadably_small_capture_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'resolution'):
            self.validate(png(), (640, 400))


if __name__ == '__main__':
    unittest.main()
