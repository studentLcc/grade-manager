from __future__ import annotations

from io import BytesIO
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import UploadFile
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

MAX_IMPORT_UPLOAD_BYTES = 5 * 1024 * 1024
SUPPORTED_IMPORT_EXTENSIONS = {".xlsx", ".xlsm"}


class ImportWorkbookError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


def load_import_workbook(file: UploadFile):
    filename = file.filename or ""
    if not any(filename.lower().endswith(extension) for extension in SUPPORTED_IMPORT_EXTENSIONS):
        raise ImportWorkbookError("仅支持 .xlsx 或 .xlsm 文件")

    data = file.file.read(MAX_IMPORT_UPLOAD_BYTES + 1)
    if len(data) > MAX_IMPORT_UPLOAD_BYTES:
        raise ImportWorkbookError("文件大小不能超过 5 MiB")

    try:
        return load_workbook(BytesIO(data), data_only=True)
    except (BadZipFile, InvalidFileException, OSError, ValueError, KeyError, ParseError) as exc:
        raise ImportWorkbookError("Excel 文件无法解析") from exc
