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
    def change_date(id,current_url,format):

        date_list = [] # [YYYY, mm, YYYYmmdd]
        length = len(format.split('/'))
        for fmat in format.split('/'):
            date_list.append(datetime.today().strftime('%'+fmat.replace('-','%')))
        format_date = '/'.join(date_list) # YYYY/mm/YYYYmmdd
        # url_front = current_url[0:current_url.rfind('/', 1) + 1]
        url_end = current_url.split('/')[-1].split('.')[-1]
        url_list = current_url.split('/')
        for i in range(0, length):
            url_list.pop()

        new_url = '/'.join(url_list) + '/' + format_date + '.' + url_end
        print(f'check url update: {new_url}\n')
        if url_updated(new_url):
            print(f'{current_url} updated to {new_url}\n')
            return new_url
        else:
            print(f'No available update for {current_url}\n')
            return current_url