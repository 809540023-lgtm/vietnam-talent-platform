"""
Translation Module - Chinese <-> Vietnamese
"""
import httpx
import os
from typing import Optional


class Translator:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")

    async def translate(self, text: str, source_lang: str = "zh-TW", target_lang: str = "vi") -> str:
        if not text or not text.strip():
            return ""
        if self.google_api_key:
            return await self._google_translate(text, source_lang, target_lang)
        return await self._free_translate(text, source_lang, target_lang)

    async def _google_translate(self, text: str, source: str, target: str) -> str:
        url = "https://translation.googleapis.com/language/translate/v2"
        params = {"key": self.google_api_key, "q": text, "source": source, "target": target, "format": "text"}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data["data"]["translations"][0]["translatedText"]
            return await self._free_translate(text, source, target)

    async def _free_translate(self, text: str, source: str, target: str) -> str:
        try:
            from googletrans import Translator as GTranslator
            t = GTranslator()
            src = "zh-tw" if source == "zh-TW" else source
            result = t.translate(text, src=src, dest=target)
            return result.text
        except Exception as e:
            print(f"Translate error: {e}")
            return text

    async def translate_job(self, job_data: dict) -> dict:
        fields = [("title_zh", "title_vi"), ("description_zh", "description_vi"),
                  ("requirements_zh", "requirements_vi"), ("benefits_zh", "benefits_vi")]
        for zh_field, vi_field in fields:
            if job_data.get(zh_field) and not job_data.get(vi_field):
                job_data[vi_field] = await self.translate(job_data[zh_field], "zh-TW", "vi")
        return job_data

    async def translate_post(self, content_zh: str) -> str:
        return await self.translate(content_zh, "zh-TW", "vi")


COMMON_TRANSLATIONS = {
    "full-time": "Toan thoi gian", "part-time": "Ban thoi gian",
    "contract": "Hop dong", "intern": "Thuc tap",
    "Taipei": "Dai Bac", "New Taipei": "Tan Bac", "Keelung": "Co Long",
    "no_requirement": "Khong yeu cau", "junior_high": "Trung hoc co so",
    "senior_high": "Trung hoc pho thong", "university": "Dai hoc",
    "basic": "Co ban", "intermediate": "Trung binh", "fluent": "Thanh thao",
    "manufacturing": "San xuat", "restaurant": "Nha hang / Am thuc",
    "service": "Dich vu", "construction": "Xay dung",
    "housing": "Co nha o", "meals": "Co bua an", "transport": "Co dua don",
    "bonus": "Thuong le tet", "overtime_pay": "Tien tang ca",
    "insurance": "Bao hiem lao dong va y te",
}


def quick_translate(text: str) -> str:
    return COMMON_TRANSLATIONS.get(text, text)
