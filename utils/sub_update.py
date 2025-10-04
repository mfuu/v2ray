#!/usr/bin/env python3

from datetime import timedelta, datetime
import json, re
import requests
from requests.adapters import HTTPAdapter

# 文件路径定义
list_path = './list.json'

with open(list_path, 'r', encoding='utf-8') as f: # 载入订阅链接
    raw_list = json.load(f)
    f.close()

def url_updated(url): # 判断远程远程链接是否已经更新
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=2))
    s.mount('https://', HTTPAdapter(max_retries=2))
    try:
        resp = s.get(url, timeout=2)
        status = resp.status_code
    except Exception:
        status = 404
    if status == 200:
        url_updated = True
    else:
        url_updated = False
    return url_updated

class update():

    def main():
        for item in raw_list:
            id = item['id']
            current_url = item['url']
            try:
                if item['update']:
                    print(f'Finding available update for ID{id}')
                    new_url = update.change_date(id,current_url,item['update'])
                    if new_url != current_url:
                        item['url'] = new_url
            except KeyError:
                print(f'{current_url} not changed! Please define update method.')

            updated_list = json.dumps(raw_list, sort_keys=False, indent=2, ensure_ascii=False)
            file = open(list_path, 'w', encoding='utf-8')
            file.write(updated_list)
            file.close()

    # 更新 url '/' 后的日期，比如 https://xxxx.com/master/YYYY/mm/YYYYmmdd.txt 中的 YYYY/mm/YYYYmmdd
    def change_date(id, current_url, date_regex):
        today = datetime.today()
        # 使用正则表达式匹配 URL 中的日期部分
        match = re.search(date_regex, current_url)
        if not match:
            print(f'No date pattern found in {current_url}\n')
            return current_url
    
        # 获取匹配到的日期字符串
        matched_date = match.group(0)
        # 构建日期格式化字符串
        format_parts = []
        num_buffer = ""
        for char in matched_date:
            if char.isdigit():
                num_buffer += char
            else:
                if num_buffer:
                    if len(num_buffer) == 4:
                        format_parts.append("%Y")
                    elif len(num_buffer) == 2:
                        format_parts.append("%m")
                    elif len(num_buffer) == 8:
                        format_parts.append("%Y%m%d")
                    else:
                        format_parts.append(num_buffer)
                    num_buffer = ""
                format_parts.append(char)
    
        # 处理最后一段数字
        if num_buffer:
            if len(num_buffer) == 4:
                format_parts.append("%Y")
            elif len(num_buffer) == 2:
                format_parts.append("%m")
            elif len(num_buffer) == 8:
                format_parts.append("%Y%m%d")
            else:
                format_parts.append(num_buffer)
    
        date_format = "".join(format_parts)
        # 生成当前日期的格式化字符串
        formatted_date = today.strftime(date_format)
        # 替换 URL 中的日期部分
        new_url = re.sub(date_regex, formatted_date, current_url)
    
        print(f'check url update: {new_url}\n')
        if url_updated(new_url):
            print(f'{current_url} updated to {new_url}\n')
            return new_url
        else:
            print(f'No available update for {current_url}\n')
            return current_url
