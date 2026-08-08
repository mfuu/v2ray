#!/usr/bin/env python3
"""订阅链接更新模块"""

import json
import re
import requests

from typing import List, Dict, Any
from datetime import datetime
from requests.adapters import HTTPAdapter


# Session
SESSION = requests.Session()
SESSION.mount("http://", HTTPAdapter(max_retries=2))
SESSION.mount("https://", HTTPAdapter(max_retries=2))


def _load_list(file_path: str) -> List[Dict[str, Any]]:
    """加载订阅链接列表"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_list(file_path: str, data: List[Dict[str, Any]]) -> None:
    """保存订阅链接列表"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=False, indent=2, ensure_ascii=False)


def _check_url_available(url: str) -> bool:
    """检查远程链接是否可用"""
    try:
        resp = SESSION.get(url, timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


class SubUpdate:
    @staticmethod
    def main(file_path: str):
        raw_list = _load_list(file_path)

        for item in raw_list:
            if not item.get("enabled", False):
                continue

            item_id = item["id"]
            current_url = item["url"]

            if "update" in item and item["update"]:
                print(f"Finding available update for ID{item_id}")
                new_url = SubUpdate._change_date(current_url, item["update"])
                if new_url != current_url:
                    item["url"] = new_url
                    print(f"{current_url} updated to {new_url}\n")
            else:
                print(f"{current_url} not changed! Update method not defined.\n")

            _save_list(file_path, raw_list)

    @staticmethod
    def _change_date(current_url, date_regex):
        """更新 url '/' 后的日期，比如 https://xxxx.com/master/YYYY/mm/YYYYmmdd.txt 中的 YYYY/mm/YYYYmmdd"""
        today = datetime.today()

        # 使用正则表达式匹配 URL 中的日期部分
        match = re.search(date_regex, current_url)
        if not match:
            print(f"No date pattern found in {current_url}\n")
            return current_url

        # 获取匹配到的日期字符串并构建格式化字符串
        matched_date = match.group(0)
        date_format = SubUpdate._build_date_format(matched_date)

        # 生成当前日期的格式化字符串
        formatted_date = today.strftime(date_format)
        # 替换 URL 中的日期部分
        new_url = re.sub(date_regex, formatted_date, current_url)

        print(f"Checking url update: {new_url}")
        if _check_url_available(new_url):
            return new_url
        else:
            print(f"No available update for {current_url}\n")
            return current_url

    @staticmethod
    def _build_date_format(date_str: str) -> str:
        """根据日期字符串构建 strftime 格式"""
        # 构建日期格式化字符串
        format_parts = []
        num_buffer = ""

        for char in date_str:
            if char.isdigit():
                num_buffer += char
            else:
                if num_buffer:
                    format_parts.append(SubUpdate._convert_num_to_format(num_buffer))
                    num_buffer = ""
                format_parts.append(char)

        # 处理最后一段数字
        if num_buffer:
            format_parts.append(SubUpdate._convert_num_to_format(num_buffer))

        return "".join(format_parts)

    @staticmethod
    def _convert_num_to_format(num_str: str) -> str:
        """将数字字符串转换为日期格式"""
        num_len = len(num_str)
        if num_len == 4:
            return "%Y"
        elif num_len == 2:
            return "%m"
        elif num_len == 8:
            return "%Y%m%d"
        return num_str
