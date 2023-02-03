#!/usr/bin/env python3

import re, yaml, json, base64
import requests, socket, urllib.parse
from requests.adapters import HTTPAdapter

import geoip2.database

class convert():

    def main(raw_input, input_type='url', output_type='url', custom_set={'dup_rm_enabled': False, 'format_name_enabled': False}): # {'input_type': ['url', 'content'],'output_type': ['url', 'YAML', 'Base64']}
        """Convert subscribe content to YAML or Base64 or url.
        首先获取到订阅内容，然后对其进行格式化处理。如果内容不是 “订阅内容解析错误”，在进行去重、改名操作后（可选）输出目标格式，否则输出 “订阅内容解析错误”。
        """
        if input_type == 'url': # 获取 URL 订阅链接内容
            sub_content = ''
            if isinstance(raw_input, list):
                a_content = []
                for url in raw_input:
                    s = requests.Session()
                    s.mount('http://', HTTPAdapter(max_retries=5))
                    s.mount('https://', HTTPAdapter(max_retries=5))
                    try:
                        print('Downloading from:' + url)
                        resp = s.get(url, timeout=5)
                        s_content = convert.yaml_decode(convert.format(resp.content.decode('utf-8')))
                        a_content.append(s_content)
                    except Exception as err:
                        print(err)
                        return 'Url 解析错误'
                sub_content = convert.format(''.join(a_content))
            else:
                s = requests.Session()
                s.mount('http://', HTTPAdapter(max_retries=5))
                s.mount('https://', HTTPAdapter(max_retries=5))
                try:
                    print('Downloading from:' + raw_input)
                    resp = s.get(raw_input, timeout=5)
                    sub_content = convert.format(resp.content.decode('utf-8'))
                except Exception as err:
                    print(err)
                    return 'Url 解析错误'
        elif input_type == 'content': # 解析订阅内容
            sub_content = convert.format(raw_input)

        if sub_content != '订阅内容解析错误':
            dup_rm_enabled = custom_set['dup_rm_enabled']
            format_name_enabled = custom_set['format_name_enabled']
            final_content = convert.makeup(sub_content,dup_rm_enabled,format_name_enabled)
            if output_type == 'YAML':
                return final_content
            elif output_type == 'Base64':
                return convert.base64_encode(convert.yaml_decode(final_content))
            elif output_type == 'url':
                return convert.yaml_decode(final_content)
            else:
                print('Please define right output type.')
                return '订阅内容解析错误'
        else:
            return '订阅内容解析错误'

    def format(sub_content,output=False): # 对链接文本(Base64, url, YAML)进行格式化处理, 输出节点的配置字典（Clash 配置）, output 为真是输出 YAML 文本
        if '</b>' not in sub_content:
            if 'proxies:' not in sub_content: # 对 URL 内容进行格式化处理
                url_list = []
                try:
                    if '://' not in sub_content:
                        sub_content = convert.base64_decode(sub_content)

                    raw_url_list = re.split(r'\n+', sub_content)

                    for url in raw_url_list:
                        while len(re.split('ss://|ssr://|vmess://|trojan://|vless://', url)) > 2:
                            url_to_split = url[8:]
                            if 'ss://' in url_to_split and 'vmess://' not in url_to_split and 'vless://' not in url_to_split:
                                url_splited = url_to_split.replace('ss://', '\nss://', 1) # https://www.runoob.com/python/att-string-replace.html
                            elif 'ssr://' in url_to_split:
                                url_splited = url_to_split.replace('ssr://', '\nssr://', 1)
                            elif 'vmess://' in url_to_split:
                                url_splited = url_to_split.replace('vmess://', '\nvmess://', 1)
                            elif 'trojan://' in url_to_split:
                                url_splited = url_to_split.replace('trojan://', '\ntrojan://', 1)
                            elif 'vless://' in url_to_split:
                                url_splited = url_to_split.replace('vless://', '\nvless://', 1)
                            url_split = url_splited.split('\n')

                            front_url = url[:8] + url_split[0]
                            url_list.append(front_url)
                            url = url_split[1]

                        url_list.append(url)

                    url_content = '\n'.join(url_list)
                    return convert.yaml_encode(url_content,output=False)
                except:
                    print('Sub_content 格式错误')
                    return '订阅内容解析错误'

            elif 'proxies:' in sub_content: # 对 Clash 内容进行格式化处理
                try:
                    try_load = yaml.safe_load(sub_content)
                    if output:
                        raise ValueError
                    else:
                        content_yaml_dic = try_load
                        for item in content_yaml_dic['proxies']:# 对转换过程中出现的不标准配置格式转换
                            try:
                                if item['type'] == 'vmess' and 'HOST' in item['ws-headers'].keys():
                                    item['ws-headers']['Host'] = item['ws-headers'].pop("HOST")
                            except KeyError:
                                if '.' not in item['server']:
                                    content_yaml_dic['proxies'].remove(item)
                                pass
                        return content_yaml_dic # 返回字典, output 值为 True 时返回修饰过的 YAML 文本
                except Exception:
                    try:
                        sub_content = sub_content.replace('\'', '').replace('"', '')
                        url_list = []
                        il_chars = ['|', '?', '[', ']', '@', '!', '%', ':']
                        lines = re.split(r'\n+', sub_content)
                        line_fix_list = []
                        for line in lines:
                            value_list = re.split(r': |, ', line)
                            if len(value_list) > 6:
                                value_list_fix = []
                                for value in value_list:
                                    for char in il_chars:
                                        value_il = False
                                        if char in value:
                                            value_il = True
                                            break
                                    if value_il == True and ('{' not in value and '}' not in value):
                                        value = '"' + value + '"'
                                        value_list_fix.append(value)
                                    elif value_il == True and '}' in value:
                                        if '}}' in value:
                                            host_part = value.replace('}}','')
                                            host_value = '"'+host_part+'"}}'
                                            value_list_fix.append(host_value)
                                        elif '}}' not in value:
                                            host_part = value.replace('}','')
                                            host_value = '"'+host_part+'"}'
                                            value_list_fix.append(host_value)
                                    else:
                                        value_list_fix.append(value)
                                    line_fix = line
                                for index in range(len(value_list_fix)):
                                    line_fix = line_fix.replace(value_list[index], value_list_fix[index])
                                line_fix_list.append(line_fix)
                            elif len(value_list) == 2:
                                value_list_fix = []
                                for value in value_list:
                                    for char in il_chars:
                                        value_il = False
                                        if char in value:
                                            value_il = True
                                            break
                                    if value_il == True:
                                        value = '"' + value + '"'
                                    value_list_fix.append(value)
                                line_fix = line
                                for index in range(len(value_list_fix)):
                                    line_fix = line_fix.replace(value_list[index], value_list_fix[index])
                                line_fix_list.append(line_fix)
                            elif len(value_list) == 1:
                                if ':' in line:
                                    line_fix_list.append(line)
                            else:
                                line_fix_list.append(line)

                        sub_content = '\n'.join(line_fix_list).replace('False', 'false').replace('True', 'true')
                        if output:
                            return sub_content
                        else:
                            content_yaml_dic = yaml.safe_load(sub_content)
                            for item in content_yaml_dic['proxies']:# 对转换过程中出现的不标准配置格式转换
                                try:
                                    if item['type'] == 'vmess' and 'HOST' in item['ws-headers'].keys():
                                        item['ws-headers']['Host'] = item['ws-headers'].pop("HOST")
                                except KeyError:
                                    if '.' not in item['server']:
                                        content_yaml_dic['proxies'].remove(item)
                                    pass

                            return content_yaml_dic # 返回字典, output 值为 True 时返回修饰过的 YAML 文本
                    except:
                        print('Sub_content 格式错误')
                        return '订阅内容解析错误'
        else:
            print('订阅内容解析错误')
            return '订阅内容解析错误'
            
    def makeup(input, dup_rm_enabled=False, format_name_enabled=False): # 输入节点配置字典, 对节点进行区域的筛选和重命名，输出 YAML 文本 
        # 区域判断(Clash YAML): https://blog.csdn.net/CSDN_duomaomao/article/details/89712826 (ip-api)
        if isinstance(input, dict):
            sub_content = input
        else:
            sub_content = convert.format(input)
        proxies_list = sub_content['proxies']
        
        if dup_rm_enabled: # 去重
            begin = 0
            raw_length = len(proxies_list)
            length = len(proxies_list)
            while begin < length:
                if (begin + 1) == 1:
                    print(f'\n-----去重开始-----\n起始数量{length}')
                elif (begin + 1) % 100 == 0:
                    print(f'当前基准{begin + 1}-----当前数量{length}')
                elif (begin + 1) == length and (begin + 1) % 100 != 0:
                    repetition = raw_length - length
                    print(f'当前基准{begin + 1}-----当前数量{length}\n重复数量{repetition}\n-----去重完成-----\n')
                proxy_compared = proxies_list[begin]

                begin_2 = begin + 1
                while begin_2 <= (length - 1):

                    if proxy_compared['server'] == proxies_list[begin_2]['server'] and proxy_compared['port'] == proxies_list[begin_2]['port']:
                        proxies_list.pop(begin_2)
                        length -= 1
                    begin_2 += 1
                begin += 1

        url_list = []

        for proxy in proxies_list: # 改名
            if format_name_enabled:
                emoji = {
                    'AD': '🇦🇩', 'AE': '🇦🇪', 'AF': '🇦🇫', 'AG': '🇦🇬', 
                    'AI': '🇦🇮', 'AL': '🇦🇱', 'AM': '🇦🇲', 'AO': '🇦🇴', 
                    'AQ': '🇦🇶', 'AR': '🇦🇷', 'AS': '🇦🇸', 'AT': '🇦🇹', 
                    'AU': '🇦🇺', 'AW': '🇦🇼', 'AX': '🇦🇽', 'AZ': '🇦🇿', 
                    'BA': '🇧🇦', 'BB': '🇧🇧', 'BD': '🇧🇩', 'BE': '🇧🇪', 
                    'BF': '🇧🇫', 'BG': '🇧🇬', 'BH': '🇧🇭', 'BI': '🇧🇮', 
                    'BJ': '🇧🇯', 'BL': '🇧🇱', 'BM': '🇧🇲', 'BN': '🇧🇳', 
                    'BO': '🇧🇴', 'BQ': '🇧🇶', 'BR': '🇧🇷', 'BS': '🇧🇸', 
                    'BT': '🇧🇹', 'BV': '🇧🇻', 'BW': '🇧🇼', 'BY': '🇧🇾', 
                    'BZ': '🇧🇿', 'CA': '🇨🇦', 'CC': '🇨🇨', 'CD': '🇨🇩', 
                    'CF': '🇨🇫', 'CG': '🇨🇬', 'CH': '🇨🇭', 'CI': '🇨🇮', 
                    'CK': '🇨🇰', 'CL': '🇨🇱', 'CM': '🇨🇲', 'CN': '🇨🇳', 
                    'CO': '🇨🇴', 'CR': '🇨🇷', 'CU': '🇨🇺', 'CV': '🇨🇻', 
                    'CW': '🇨🇼', 'CX': '🇨🇽', 'CY': '🇨🇾', 'CZ': '🇨🇿', 
                    'DE': '🇩🇪', 'DJ': '🇩🇯', 'DK': '🇩🇰', 'DM': '🇩🇲', 
                    'DO': '🇩🇴', 'DZ': '🇩🇿', 'EC': '🇪🇨', 'EE': '🇪🇪', 
                    'EG': '🇪🇬', 'EH': '🇪🇭', 'ER': '🇪🇷', 'ES': '🇪🇸', 
                    'ET': '🇪🇹', 'EU': '🇪🇺', 'FI': '🇫🇮', 'FJ': '🇫🇯', 
                    'FK': '🇫🇰', 'FM': '🇫🇲', 'FO': '🇫🇴', 'FR': '🇫🇷', 
                    'GA': '🇬🇦', 'GB': '🇬🇧', 'GD': '🇬🇩', 'GE': '🇬🇪', 
                    'GF': '🇬🇫', 'GG': '🇬🇬', 'GH': '🇬🇭', 'GI': '🇬🇮', 
                    'GL': '🇬🇱', 'GM': '🇬🇲', 'GN': '🇬🇳', 'GP': '🇬🇵', 
                    'GQ': '🇬🇶', 'GR': '🇬🇷', 'GS': '🇬🇸', 'GT': '🇬🇹', 
                    'GU': '🇬🇺', 'GW': '🇬🇼', 'GY': '🇬🇾', 'HK': '🇭🇰', 
                    'HM': '🇭🇲', 'HN': '🇭🇳', 'HR': '🇭🇷', 'HT': '🇭🇹', 
                    'HU': '🇭🇺', 'ID': '🇮🇩', 'IE': '🇮🇪', 'IL': '🇮🇱', 
                    'IM': '🇮🇲', 'IN': '🇮🇳', 'IO': '🇮🇴', 'IQ': '🇮🇶', 
                    'IR': '🇮🇷', 'IS': '🇮🇸', 'IT': '🇮🇹', 'JE': '🇯🇪', 
                    'JM': '🇯🇲', 'JO': '🇯🇴', 'JP': '🇯🇵', 'KE': '🇰🇪', 
                    'KG': '🇰🇬', 'KH': '🇰🇭', 'KI': '🇰🇮', 'KM': '🇰🇲', 
                    'KN': '🇰🇳', 'KP': '🇰🇵', 'KR': '🇰🇷', 'KW': '🇰🇼', 
                    'KY': '🇰🇾', 'KZ': '🇰🇿', 'LA': '🇱🇦', 'LB': '🇱🇧', 
                    'LC': '🇱🇨', 'LI': '🇱🇮', 'LK': '🇱🇰', 'LR': '🇱🇷', 
                    'LS': '🇱🇸', 'LT': '🇱🇹', 'LU': '🇱🇺', 'LV': '🇱🇻', 
                    'LY': '🇱🇾', 'MA': '🇲🇦', 'MC': '🇲🇨', 'MD': '🇲🇩', 
                    'ME': '🇲🇪', 'MF': '🇲🇫', 'MG': '🇲🇬', 'MH': '🇲🇭', 
                    'MK': '🇲🇰', 'ML': '🇲🇱', 'MM': '🇲🇲', 'MN': '🇲🇳', 
                    'MO': '🇲🇴', 'MP': '🇲🇵', 'MQ': '🇲🇶', 'MR': '🇲🇷', 
                    'MS': '🇲🇸', 'MT': '🇲🇹', 'MU': '🇲🇺', 'MV': '🇲🇻', 
                    'MW': '🇲🇼', 'MX': '🇲🇽', 'MY': '🇲🇾', 'MZ': '🇲🇿', 
                    'NA': '🇳🇦', 'NC': '🇳🇨', 'NE': '🇳🇪', 'NF': '🇳🇫', 
                    'NG': '🇳🇬', 'NI': '🇳🇮', 'NL': '🇳🇱', 'NO': '🇳🇴', 
                    'NP': '🇳🇵', 'NR': '🇳🇷', 'NU': '🇳🇺', 'NZ': '🇳🇿', 
                    'OM': '🇴🇲', 'PA': '🇵🇦', 'PE': '🇵🇪', 'PF': '🇵🇫', 
                    'PG': '🇵🇬', 'PH': '🇵🇭', 'PK': '🇵🇰', 'PL': '🇵🇱', 
                    'PM': '🇵🇲', 'PN': '🇵🇳', 'PR': '🇵🇷', 'PS': '🇵🇸', 
                    'PT': '🇵🇹', 'PW': '🇵🇼', 'PY': '🇵🇾', 'QA': '🇶🇦', 
                    'RE': '🇷🇪', 'RO': '🇷🇴', 'RS': '🇷🇸', 'RU': '🇷🇺', 
                    'RW': '🇷🇼', 'SA': '🇸🇦', 'SB': '🇸🇧', 'SC': '🇸🇨', 
                    'SD': '🇸🇩', 'SE': '🇸🇪', 'SG': '🇸🇬', 'SH': '🇸🇭', 
                    'SI': '🇸🇮', 'SJ': '🇸🇯', 'SK': '🇸🇰', 'SL': '🇸🇱', 
                    'SM': '🇸🇲', 'SN': '🇸🇳', 'SO': '🇸🇴', 'SR': '🇸🇷', 
                    'SS': '🇸🇸', 'ST': '🇸🇹', 'SV': '🇸🇻', 'SX': '🇸🇽', 
                    'SY': '🇸🇾', 'SZ': '🇸🇿', 'TC': '🇹🇨', 'TD': '🇹🇩', 
                    'TF': '🇹🇫', 'TG': '🇹🇬', 'TH': '🇹🇭', 'TJ': '🇹🇯', 
                    'TK': '🇹🇰', 'TL': '🇹🇱', 'TM': '🇹🇲', 'TN': '🇹🇳', 
                    'TO': '🇹🇴', 'TR': '🇹🇷', 'TT': '🇹🇹', 'TV': '🇹🇻', 
                    'TW': '🇹🇼', 'TZ': '🇹🇿', 'UA': '🇺🇦', 'UG': '🇺🇬', 
                    'UM': '🇺🇲', 'US': '🇺🇸', 'UY': '🇺🇾', 'UZ': '🇺🇿', 
                    'VA': '🇻🇦', 'VC': '🇻🇨', 'VE': '🇻🇪', 'VG': '🇻🇬', 
                    'VI': '🇻🇮', 'VN': '🇻🇳', 'VU': '🇻🇺', 'WF': '🇼🇫', 
                    'WS': '🇼🇸', 'XK': '🇽🇰', 'YE': '🇾🇪', 'YT': '🇾🇹', 
                    'ZA': '🇿🇦', 'ZM': '🇿🇲', 'ZW': '🇿🇼', 
                    'RELAY': '🏁',
                    'NOWHERE': '🇦🇶',
                }

                server = proxy['server']
                if server.replace('.','').isdigit():
                    ip = server
                else:
                    try:
                        ip = socket.gethostbyname(server) # https://cloud.tencent.com/developer/article/1569841
                    except Exception:
                        ip = server

                with geoip2.database.Reader('./utils/Country.mmdb') as ip_reader:
                    try:
                        response = ip_reader.country(ip)
                        country_code = response.country.iso_code
                    except Exception:
                        ip = '0.0.0.0'
                        country_code = 'NOWHERE'

                if country_code == 'CLOUDFLARE':
                    country_code = 'RELAY'
                elif country_code == 'PRIVATE':
                    country_code = 'RELAY'

                if country_code in emoji:
                    name_emoji = emoji[country_code]
                else:
                    name_emoji = emoji['NOWHERE']

                proxy_index = proxies_list.index(proxy)
                if len(proxies_list) >= 999:
                    proxy['name'] = f'{name_emoji}{country_code}-{ip}-{proxy_index:0>4d}'
                elif len(proxies_list) <= 999 and len(proxies_list) > 99:
                    proxy['name'] = f'{name_emoji}{country_code}-{ip}-{proxy_index:0>3d}'
                elif len(proxies_list) <= 99:
                    proxy['name'] = f'{name_emoji}{country_code}-{ip}-{proxy_index:0>2d}'

                if proxy['server'] != '127.0.0.1':
                    proxy_str = str(proxy)
                    url_list.append(proxy_str)
            elif format_name_enabled == False:
                if proxy['server'] != '127.0.0.1': # 防止加入无用节点
                    proxy_str = str(proxy)
                    url_list.append(proxy_str)

        yaml_content_dic = {'proxies': url_list}
        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2) # yaml.dump 显示中文方法 https://blog.csdn.net/weixin_41548578/article/details/90651464 yaml.dump 各种参数 https://blog.csdn.net/swinfans/article/details/88770119
        yaml_content = convert.format(yaml_content_raw,output=True)
        
        return yaml_content # 输出 YAML 格式文本

    def yaml_encode(url_content,output=True): # 将 URL 内容转换为 YAML 文本, output 为 False 时输出节点配置字典
        url_list = []

        lines = re.split(r'\n+', url_content)

        for line in lines:
            yaml_url = {}
            if 'vmess://' in line:
                try:
                    vmess_json_config = json.loads(convert.base64_decode(line.replace('vmess://', '')))
                    vmess_default_config = {
                        'v': 'Vmess Node', 'ps': 'Vmess Node', 'add': '0.0.0.0', 'port': 0, 'id': '',
                        'aid': 0, 'scy': 'auto', 'net': '', 'type': '', 'host': vmess_json_config['add'], 'path': '/', 'tls': ''
                    }
                    vmess_default_config.update(vmess_json_config)
                    vmess_config = vmess_default_config

                    yaml_url = {}
                    #yaml_config_str = ['name', 'server', 'port', 'type', 'uuid', 'alterId', 'cipher', 'tls', 'skip-cert-verify', 'network', 'ws-path', 'ws-headers']
                    #vmess_config_str = ['ps', 'add', 'port', 'id', 'aid', 'scy', 'tls', 'net', 'host', 'path']
                    # 生成 yaml 节点字典
                    if vmess_config['id'] == '' or vmess_config['id'] is None:
                        print('节点格式错误')
                    else:
                        yaml_url.setdefault('name', urllib.parse.unquote(str(vmess_config['ps'])))
                        yaml_url.setdefault('server', vmess_config['add'])
                        yaml_url.setdefault('port', int(vmess_config['port']))
                        yaml_url.setdefault('type', 'vmess')
                        yaml_url.setdefault('uuid', vmess_config['id'])
                        yaml_url.setdefault('alterId', int(vmess_config['aid']))
                        yaml_url.setdefault('cipher', vmess_config['scy'])
                        yaml_url.setdefault('skip-cert-verify', True)
                        if vmess_config['net'] == '' or vmess_config['net'] is False or vmess_config['net'] is None:
                            yaml_url.setdefault('network', 'tcp')
                        else:
                            yaml_url.setdefault('network', vmess_config['net'])
                        if vmess_config['path'] == '' or vmess_config['path'] is False or vmess_config['path'] is None:
                            yaml_url.setdefault('ws-path', '/')
                        else:
                            yaml_url.setdefault('ws-path', vmess_config['path'])
                        if vmess_config['net'] == 'h2' or vmess_config['net'] == 'grpc':
                            yaml_url.setdefault('tls', True)
                        elif vmess_config['tls'] == '' or vmess_config['tls'] is False or vmess_config['tls'] is None:
                            yaml_url.setdefault('tls', False)
                        else:
                            yaml_url.setdefault('tls', True)
                        if vmess_config['host'] == '':
                            yaml_url.setdefault('ws-headers', {'Host': vmess_config['add']})
                        else:
                            yaml_url.setdefault('ws-headers', {'Host': vmess_config['host']})

                        url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 vmess 节点发生错误: {err}')
                    pass

            if 'ss://' in line and 'vless://' not in line and 'vmess://' not in line:
                if '#' not in line:
                    line = line + '#SS%20Node'
                try:
                    ss_content =  line.replace('ss://', '')
                    part_list = ss_content.split('#', 1) # https://www.runoob.com/python/att-string-split.html
                    yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))
                    if '@' in part_list[0]:
                        mix_part = part_list[0].split('@', 1)
                        method_part = convert.base64_decode(mix_part[0])
                        server_part = f'{method_part}@{mix_part[1]}'
                    else:
                        server_part = convert.base64_decode(part_list[0])

                    server_part_list = server_part.split(':', 1) # 使用多个分隔符 https://blog.csdn.net/shidamowang/article/details/80254476 https://zhuanlan.zhihu.com/p/92287240
                    method_part = server_part_list[0]
                    server_part_list = server_part_list[1].rsplit('@', 1)
                    password_part = server_part_list[0]
                    server_part_list = server_part_list[1].split(':', 1)

                    yaml_url.setdefault('server', server_part_list[0])
                    yaml_url.setdefault('port', server_part_list[1])
                    yaml_url.setdefault('type', 'ss')
                    yaml_url.setdefault('cipher', method_part)
                    yaml_url.setdefault('password', password_part)

                    url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 ss 节点发生错误: {err}')
                    pass

            if 'ssr://' in line:
                try:
                    ssr_content = convert.base64_decode(line.replace('ssr://', ''))
                
                    parts = re.split(':', ssr_content)
                    if len(parts) != 6:
                        print('SSR 格式错误: %s' % ssr_content)
                    password_and_params = parts[5]
                    password_and_params = re.split('/\?', password_and_params)
                    password_encode_str = password_and_params[0]
                    params = password_and_params[1]

                    param_parts = re.split('\&', params)
                    param_dic = {}
                    for part in param_parts:
                        key_and_value = re.split('\=', part)
                        param_dic[key_and_value[0]] = key_and_value[1]
                    yaml_url.setdefault('name', convert.base64_decode(param_dic['remarks']))
                    yaml_url.setdefault('server', parts[0])
                    yaml_url.setdefault('port', parts[1])
                    yaml_url.setdefault('type', 'ssr')
                    yaml_url.setdefault('cipher', parts[3])
                    yaml_url.setdefault('password', convert.base64_decode(password_encode_str))
                    yaml_url.setdefault('obfs', parts[4])
                    yaml_url.setdefault('protocol', parts[2])
                    yaml_url.setdefault('obfsparam', convert.base64_decode(param_dic['obfsparam']))
                    yaml_url.setdefault('protoparam', convert.base64_decode(param_dic['protoparam']))
                    yaml_url.setdefault('group', convert.base64_decode(param_dic['group']))

                    url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 ssr 节点发生错误: {err}')
                    pass

            if 'trojan://' in line:
                try:
                    url_content = line.replace('trojan://', '')
                    part_list = re.split('#', url_content, maxsplit=1) # https://www.runoob.com/python/att-string-split.html
                    yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))

                    server_part = part_list[0].replace('trojan://', '')
                    server_part_list = re.split(':|@|\?|&', server_part) # 使用多个分隔符 https://blog.csdn.net/shidamowang/article/details/80254476 https://zhuanlan.zhihu.com/p/92287240
                    yaml_url.setdefault('server', server_part_list[1])
                    yaml_url.setdefault('port', server_part_list[2])
                    yaml_url.setdefault('type', 'trojan')
                    yaml_url.setdefault('password', server_part_list[0])
                    server_part_list = server_part_list[3:]

                    for config in server_part_list:
                        if 'sni=' in config:
                            yaml_url.setdefault('sni', config[4:])
                        elif 'allowInsecure=' in config or 'tls=' in config:
                            if config[-1] == 0:
                                yaml_url.setdefault('tls', False)
                        elif 'type=' in config:
                            if config[5:] != 'tcp':
                                yaml_url.setdefault('network', config[5:])
                        elif 'path=' in config:
                            yaml_url.setdefault('ws-path', config[5:])
                        elif 'security=' in config:
                            if config[9:] != 'tls':
                                yaml_url.setdefault('tls', False)

                    yaml_url.setdefault('skip-cert-verify', True)

                    url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 trojan 节点发生错误: {err}')
                    pass

        yaml_content_dic = {'proxies': url_list}
        if output:
            yaml_content = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2)
        else:
            yaml_content = yaml_content_dic
        return yaml_content
    def base64_encode(url_content): # 将 URL 内容转换为 Base64
        base64_content = base64.b64encode(url_content.encode('utf-8')).decode('ascii')
        return base64_content

    def yaml_decode(url_content): # YAML 文本转换为 URL 链接内容
        try:
            if isinstance(url_content, dict):
                sub_content = url_content
            else:
                sub_content = convert.format(url_content)
            proxies_list = sub_content['proxies']

            protocol_url = []
            for index in range(len(proxies_list)): # 不同节点订阅链接内容 https://github.com/hoochanlon/fq-book/blob/master/docs/append/srvurl.md
                proxy = proxies_list[index]

                if proxy['type'] == 'vmess': # Vmess 节点提取, 由 Vmess 所有参数 dump JSON 后 base64 encode 得来。

                    yaml_default_config = {
                        'name': 'Vmess Node', 'server': '0.0.0.0', 'port': 0, 'uuid': '', 'alterId': 0,
                        'cipher': 'auto', 'network': 'ws', 'ws-headers': {'Host': proxy['server']},
                        'ws-path': '/', 'tls': '', 'sni': ''
                    }

                    yaml_default_config.update(proxy)
                    proxy_config = yaml_default_config

                    vmess_value = {
                        'v': 2, 'ps': proxy_config['name'], 'add': proxy_config['server'],
                        'port': proxy_config['port'], 'id': proxy_config['uuid'], 'aid': proxy_config['alterId'],
                        'scy': proxy_config['cipher'], 'net': proxy_config['network'], 'type': None, 'host': proxy_config['ws-headers']['Host'],
                        'path': proxy_config['ws-path'], 'tls': proxy_config['tls'], 'sni': proxy_config['sni']
                        }

                    vmess_raw_proxy = json.dumps(vmess_value, sort_keys=False, indent=2, ensure_ascii=False)
                    vmess_proxy = str('vmess://' + convert.base64_encode(vmess_raw_proxy) + '\n')
                    protocol_url.append(vmess_proxy)

                elif proxy['type'] == 'ss': # SS 节点提取, 由 ss_base64_decoded 部分(参数: 'cipher', 'password', 'server', 'port') Base64 编码后 加 # 加注释(URL_encode) 
                    ss_base64_decoded = str(proxy['cipher']) + ':' + str(proxy['password']) + '@' + str(proxy['server']) + ':' + str(proxy['port'])
                    ss_base64 = convert.base64_encode(ss_base64_decoded)
                    ss_proxy = str('ss://' + ss_base64 + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                    protocol_url.append(ss_proxy)

                elif proxy['type'] == 'trojan': # Trojan 节点提取, 由 trojan_proxy 中参数再加上 # 加注释(URL_encode) # trojan Go https://p4gefau1t.github.io/trojan-go/developer/url/
                    if 'tls' in proxy.keys() and 'network' in proxy.keys():
                        if proxy['tls'] == True and proxy['network'] != 'tcp':
                            network_type = proxy['network']
                            trojan_go = f'?security=tls&type={network_type}&headerType=none'
                        elif proxy['tls'] == False and proxy['network'] != 'tcp':
                            trojan_go = f'??allowInsecure=0&type={network_type}&headerType=none'
                    else:
                        trojan_go = '?allowInsecure=1'
                    if 'sni' in proxy.keys():
                        trojan_go = trojan_go+'&sni='+proxy['sni']
                    trojan_proxy = str('trojan://' + str(proxy['password']) + '@' + str(proxy['server']) + ':' + str(proxy['port']) + trojan_go + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                    protocol_url.append(trojan_proxy)
                
                elif proxy['type'] == 'ssr': # ssr 节点提取, 由 ssr_base64_decoded 中所有参数总体 base64 encode
                    remarks = convert.base64_encode(proxy['name']).replace('+', '-')
                    server = proxy['server']
                    port = str(proxy['port'])
                    password = convert.base64_encode(proxy['password'])
                    cipher = proxy['cipher']
                    protocol = proxy['protocol']
                    obfs = proxy['obfs']
                    for key in {'group', 'obfsparam', 'protoparam'}:
                        if key in proxy:
                            if key == 'group':
                                group = convert.base64_encode(proxy[key])
                            elif key == 'obfsparam':
                                obfsparam = convert.base64_encode(proxy[key])
                            elif key == 'protoparam':
                                protoparam = convert.base64_encode(proxy[key])
                        else:
                            if key == 'group':
                                group = 'U1NSUHJvdmlkZXI'
                            elif key == 'obfsparam':
                                obfsparam = ''
                            elif key == 'protoparam':
                                protoparam = ''

                    ssr_proxy = 'ssr://'+convert.base64_encode(server+':'+port+':'+protocol+':'+cipher+':'+obfs+':'+password+'/?group='+group+'&remarks='+remarks+'&obfsparam='+obfsparam+'&protoparam='+protoparam+'\n')
                    protocol_url.append(ssr_proxy)

            yaml_content = ''.join(protocol_url)
            return yaml_content
        except Exception as err:
            print(f'yaml decode 发生 {err} 错误')
            return '订阅内容解析错误'

    def base64_decode(url_content): # Base64 转换为 URL 链接内容
        if '-' in url_content:
            url_content = url_content.replace('-', '+')
        if '_' in url_content:
            url_content = url_content.replace('_', '/')
        #print(len(url_content))
        missing_padding = len(url_content) % 4
        if missing_padding != 0:
            url_content += '='*(4 - missing_padding) # 不是4的倍数后加= https://www.cnblogs.com/wswang/p/7717997.html
        try:
            base64_content = base64.b64decode(url_content.encode('utf-8')).decode('utf-8','ignore') # https://www.codenong.com/42339876/
            base64_content_format = base64_content
            return base64_content_format
        except UnicodeDecodeError:
            base64_content = base64.b64decode(url_content)
            base64_content_format = base64_content
            return str(base64_content)

    def convert_remote(url='', output_type='clash', host='http://127.0.0.1:25500'): #{url='订阅链接', output_type={'clash': 输出 Clash 配置, 'base64': 输出 Base64 配置, 'url': 输出 url 配置}, host='远程订阅转化服务地址'}
        # 使用远程订阅转换服务，输出相应配置。
        sever_host = host
        url = urllib.parse.quote(url, safe='') # https://docs.python.org/zh-cn/3/library/urllib.parse.html
        if output_type == 'clash':
            converted_url = sever_host+'/sub?target=clash&url='+url+'&insert=false&emoji=true&list=true'
            try:
                resp = requests.get(converted_url)
            except Exception as err:
                print(err)
                return 'Url 解析错误'
            if resp.text == 'No nodes were found!':
                sub_content = 'Url 解析错误'
            else:
                sub_content = convert.makeup(convert.format(resp.text), dup_rm_enabled=False, format_name_enabled=True)
        elif output_type == 'base64':
            converted_url = sever_host+'/sub?target=mixed&url='+url+'&insert=false&emoji=true&list=true'
            try:
                resp = requests.get(converted_url)
            except Exception as err:
                print(err)
                return 'Url 解析错误'
            if resp.text == 'No nodes were found!':
                sub_content = 'Url 解析错误'
            else:
                sub_content = convert.base64_encode(resp.text)
        elif output_type == 'url':
            converted_url = sever_host+'/sub?target=mixed&url='+url+'&insert=false&emoji=true&list=true'
            try:
                resp = requests.get(converted_url)
            except Exception as err:
                print(err)
                return 'Url 解析错误'
            if resp.text == 'No nodes were found!':
                sub_content = 'Url 解析错误'
            else:
                sub_content = resp.text

        return sub_content
