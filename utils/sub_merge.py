#!/usr/bin/env python3

from sub_convert import convert
from sub_update import update

import re, json, os
from io import BytesIO
from urllib import request

list_path = './list.json'
merge_path = './merge'
export_path = './merge/list'


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
  def main(url_list):
    content_list = []

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
          print(f'Writing error of {remark} to {ids:0>2d}.txt because of Url 解析错误\n')
      elif content == 'Url 订阅内容无法解析':
        print(f'Writing error of {remark} to {ids:0>2d}.txt because of Url 订阅内容无法解析\n')
      elif content != None:
        content_list.append(content)
        print(f'Writing content of {remark} to {ids:0>2d}.txt\n')
      else:
        print(f'Writing error of {remark} to {ids:0>2d}.txt because of Url 订阅内容无法解析\n')
    print('Merging nodes...\n')
    content_raw = ''.join(content_list) # https://python3-cookbook.readthedocs.io/zh_CN/latest/c02/p14_combine_and_concatenate_strings.html
    content_clash = convert.main(content_raw,'content','YAML',{'dup_rm_enabled': False, 'format_name_enabled': True})
    content_base64 = convert.base64_encode(content_raw)
    content = content_raw

    def content_write(file, output_type):
      file = open(file, 'w+', encoding = 'utf-8')
      file.write(output_type)
      file.close
    
    write_list = [f'{merge_path}/merge.txt', f'{merge_path}/merge_base64.txt', f'{merge_path}/merge_clash.yaml']
    content_type = (content, content_base64, content_clash)
    for index in range(len(write_list)):
      content_write(write_list[index], content_type[index])

    content_write(f'./v2ray', content_base64) # 根目录订阅文件写入
    content_write(f'./clash.yaml', content_clash)
    print('Done!\n')

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
  update.main()
  merge.geoip_update('https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb')

  list = merge.read_as_list(list_path)
  list_remote = merge.read_as_list(list_path, True)
  merge.main(list_remote)