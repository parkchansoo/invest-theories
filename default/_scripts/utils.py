#!/usr/bin/env python3
"""
공통 유틸리티 함수
다른 스크립트에서 `from utils import clean_company_name` 으로 사용
"""


def clean_company_name(name: str) -> str:
    """회사명에서 법인 접미사 제거 및 파일명 안전 문자로 변환.

    예시:
        "NVIDIA Corporation" -> "NVIDIA"
        "Linde plc"          -> "Linde"
        "Air Products and Chemicals, Inc." -> "AirProducts"
        "삼성전자"            -> "삼성전자"
    """
    for suffix in [", Inc.", " Inc.", " Inc", " Corporation", " Corp.",
                   " Corp", " Ltd.", " Ltd", " plc", " PLC",
                   " Co.", " Co", " Company", " Technologies",
                   " Holdings", " Group", " and Chemicals",
                   " S.A.", " SE", " N.V.", " AG"]:
        name = name.replace(suffix, "")
    name = name.strip().replace(" ", "").replace(",", "").replace(".", "")
    name = name.replace("/", "-").replace("\\", "-")
    return name
