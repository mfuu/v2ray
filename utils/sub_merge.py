#!/usr/bin/env python3
"""订阅内容合并模块"""

import re
import json
from typing import List, Dict, Any
from urllib import request

from sub_convert import SubConvert
from sub_update import SubUpdate

# 文件路径定义
LIST_PATH = "./list.json"


class SubMerge:
    @staticmethod
    def geoip_update(url: str) -> None:
        """更新 GeoIP 数据库"""
        print("Downloading Country.mmdb...")
        try:
            request.urlretrieve(url, "./utils/Country.mmdb")
            print("Success!\n")
        except Exception:
            print("Failed!\n")

    @staticmethod
    def main(url_list: List[Dict[str, Any]]) -> None:
        """将转换后的所有 Url 链接内容合并转换 YAML or Base64，并输出文件"""
        content_list = []

        for index, item in enumerate(url_list):
            content = SubConvert.convert_remote(item["url"], "url", "http://127.0.0.1:25500")
            item_id = item["id"]
            remark = item["remark"]

            if content == "Url 解析错误":
                content = SubConvert.main(SubMerge.read_as_list(LIST_PATH)[index]["url"], "url", "url")
                if content != "Url 解析错误":
                    content_list.append(content)
                    print(f"Writing content of {remark} to {item_id:0>2d}.txt\n")
                else:
                    print(f"Writing error of {remark} to {item_id:0>2d}.txt because of Url 解析错误\n")
            elif content == "Url 订阅内容无法解析":
                print(f"Writing error of {remark} to {item_id:0>2d}.txt because of Url 订阅内容无法解析\n")
            elif content is not None:
                content_list.append(content)
                print(f"Writing content of {remark} to {item_id:0>2d}.txt\n")
            else:
                print(f"Writing error of {remark} to {item_id:0>2d}.txt because of Url 订阅内容无法解析\n")

        print("Merging nodes...\n")
        content_raw = "".join(content_list)
        content_clash = SubConvert.main(content_raw, "content", "YAML", {"dup_rm_enabled": False, "format_name_enabled": True})
        content_base64 = SubConvert.base64_encode(content_raw)

        SubMerge._write_content("./v2ray", content_base64)  # 根目录订阅文件写入
        SubMerge._write_content("./clash.yaml", content_clash)
        print("Done!\n")

    @staticmethod
    def _write_content(file_path: str, content: str) -> None:
        """写入内容到文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def read_as_list(file_path: str, remote: bool = False) -> List[Dict[str, Any]]:
        """将 list.json Url 内容读取为列表"""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)

        input_list = []
        for item in raw_list:
            if item.get("enabled", False):
                if not remote:
                    urls = re.split("\|", item["url"])
                else:
                    urls = item["url"]
                item["url"] = urls
                input_list.append(item)
        return input_list


if __name__ == "__main__":
    SubUpdate.main(LIST_PATH)
    SubMerge.geoip_update("https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb")

    url_list = SubMerge.read_as_list(LIST_PATH)
    url_list_remote = SubMerge.read_as_list(LIST_PATH, True)
    SubMerge.main(url_list_remote)
