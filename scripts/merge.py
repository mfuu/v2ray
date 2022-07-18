#!/usr/bin/env python3

from convert import convert

import re, json, os
from io import BytesIO
from urllib import request

list_path = './list.json'
export_path = './list'


class merge(): 

  def geoip_update(url):
    print('Downloading Country.mmdb...')
    try:
        request.urlretrieve(url, './utils/Country.mmdb')
        print('Success!\n')
    except Exception:
        print('Failed!\n')
        pass

  # 将转换后的所有 Url 链接内容合并转换 YAML or Base64, ，并输出文件，输入订阅列表。
  def merge(url_list):
    content_list = []
    for t in os.walk(export_path):
      for f in t[2]:
        f = t[0] + f
        os.remove(f)

    for index in range(len(url_list)):
      content = convert.convert_remote(url_list[index]['url'], 'url', 'http://127.0.0.1:25500')
      ids = url_list[index]['id']
      remark = url_list[index]['remark']
      if content == 'Url 解析错误':
        content = convert.main(merge.read_as_list(list_path)[index]['url'],'url','url')
        if content != 'Url 解析错误':
          content_list.append(content)
          print(f'Writing content of {remark} to {ids:0>2d}.txt\n')
        else:
          print(f'Writing error of {remark} to {ids:0>2d}.txt\n')
          file = open(f'{export_path}{ids:0>2d}.txt', 'w+', encoding= 'utf-8')
          file.write('Url 解析错误')
          file.close()
      elif content == 'Url 订阅内容无法解析':
        file = open(f'{export_path}{ids:0>2d}.txt', 'w+', encoding= 'utf-8')
        file.write('Url 订阅内容无法解析')
        file.close()
        print(f'Writing error of {remark} to {ids:0>2d}.txt\n')
      elif content != None:
        content_list.append(content)
        file = open(f'{export_path}{ids:0>2d}.txt', 'W+', encoding='utf-8')
        file.write('url 解析错误')
        file.close()
        print(f'Writing content of {remark} to {ids:0>2d}.txt\n')
      else:
        file = open(f'{export_path}{ids:0>2d}.txt', 'W+', encoding='utf-8')
        file.write('url 订阅内容无法解析')
        file.close()
        print(f'Writing error of {remark} to {ids:0>2d}.txt\n')

  # 将 list.json Url 内容读取为列表
  def read_as_list(file_path, remote = False):
    with open(file_path, 'r', encoding='utf-8') as f:
      raw_list = json.load(f)
    input_list = []
    for index in range(len(raw_list)):
      if raw_list[index]['enabled']:
        if remote == False:
          urls = re.split('\|', raw_list[index]['url'])
        else:
          urls = raw_list[index]['url']
        raw_list[index]['url'] = urls
        input_list.append(raw_list[index])
    return input_list


if __name__ == '__main__':
  merge.geoip_update('https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb')

  list = merge.read_as_list(list_path)
  list_remote = merge.read_as_list(list_path, True)
  merge.merge(list_remote)