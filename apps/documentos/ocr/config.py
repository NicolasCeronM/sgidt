# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    TESSERACT_CMD: str | None = os.getenv("TESSERACT_CMD")
    POPPLER_PATH: str | None = os.getenv("POPPLER_PATH")
    TESSERACT_LANG: str = os.getenv("TESSERACT_LANG", "spa+eng")
    TESSERACT_PSM: str = os.getenv("TESSERACT_PSM", "6")
    TESSERACT_OEM: str = os.getenv("TESSERACT_OEM", "3")
    TESSERACT_PSM_IMAGE: str = os.getenv("TESSERACT_PSM_IMAGE", "4")

settings = Settings()
