# -*- coding: utf-8 -*-
"""
腾讯云函数 (SCF) 通用代理服务
类似 Vercel 万能反代，通过 URL 路径指定目标地址

使用方式:
  https://你的函数URL地址/https/api.imdbapi.dev/search/titles?query=test
  https://你的函数URL地址/http/example.com/api/data

部署方式:
  1. 在腾讯云函数控制台创建事件函数
  2. 运行环境选择 Python 3.9
  3. 上传此文件
  4. 启用函数 URL (无需 API 网关)

函数 URL 文档: https://cloud.tencent.com/document/product/583/96099
"""

import json
import re
import os
import urllib.request
import urllib.parse
import urllib.error
from urllib.parse import urlencode
import time

# 地域映射
REGION_MAP = {
    'ap-guangzhou': '广州',
    'ap-shanghai': '上海',
    'ap-beijing': '北京',
    'ap-chengdu': '成都',
    'ap-chongqing': '重庆',
    'ap-hongkong': '香港',
    'ap-singapore': '新加坡',
    'ap-mumbai': '孟买',
    'ap-seoul': '首尔',
    'ap-bangkok': '曼谷',
    'ap-tokyo': '东京',
    'na-siliconvalley': '硅谷',
    'na-ashburn': '弗吉尼亚',
    'na-toronto': '多伦多',
    'eu-frankfurt': '法兰克福',
    'eu-moscow': '莫斯科',
}

# 请求日志 (内存存储，最多保留 50 条)
REQUEST_LOGS = []
MAX_LOGS = 50

def add_log(method, url, status, elapsed_ms, error=None):
    """添加请求日志"""
    from datetime import datetime
    log_entry = {
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'method': method,
        'url': url,
        'status': status,
        'elapsed_ms': elapsed_ms
    }
    if error:
        log_entry['error'] = error

    REQUEST_LOGS.insert(0, log_entry)
    # 保留最近 50 条
    while len(REQUEST_LOGS) > MAX_LOGS:
        REQUEST_LOGS.pop()

def get_proxy_ip():
    """获取云函数出口 IP"""
    try:
        req = urllib.request.Request(
            'https://httpbin.org/ip',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('origin', 'Unknown')
    except:
        try:
            # 备用方案
            req = urllib.request.Request(
                'https://api.ipify.org?format=json',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('ip', 'Unknown')
        except:
            return 'Unknown'

def main_handler(event, context):
    """腾讯云函数入口"""

    # 获取请求路径
    path = event.get('path', '/')
    query_string = event.get('queryString', {})
    method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    body = event.get('body', '')

    # 首页 - 显示代理 IP 和地域信息
    if path == '/' or path == '' or path == '/release' or path == '/release/':
        # 获取云函数出口 IP
        proxy_ip = get_proxy_ip()

        # 获取云函数地域
        scf_region = os.environ.get('TENCENTCLOUD_REGION', 'Unknown')
        region_name = REGION_MAP.get(scf_region, scf_region)

        # 获取函数信息
        func_name = os.environ.get('SCF_FUNCTIONNAME', 'Unknown')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'service': '通用代理服务 (腾讯云函数)',
                'status': '运行中',
                'proxy_ip': proxy_ip,
                'proxy_region': region_name,
                'proxy_region_code': scf_region,
                'function_name': func_name,
                'usage': '/https/域名/路径 或 /http/域名/路径',
                'examples': [
                    '/https/api.imdbapi.dev/search/titles?query=test',
                    '/https/api.github.com/users/octocat',
                    '/https/httpbin.org/ip'
                ],
                'recent_logs': REQUEST_LOGS[:20]  # 显示最近 20 条日志
            }, ensure_ascii=False, indent=2)
        }

    # 解析目标 URL
    # 格式: /https/domain.com/path 或 /http/domain.com/path
    match = re.match(r'^/(https?)/(.+)$', path)

    if not match:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Invalid URL format',
                'usage': '/https/domain.com/path or /http/domain.com/path',
                'example': '/https/api.imdbapi.dev/search/titles?query=test'
            })
        }
    
    protocol = match.group(1)
    target_path = match.group(2)
    
    # 构建目标 URL
    target_url = f"{protocol}://{target_path}"
    
    # 添加查询参数
    if query_string:
        query_str = urlencode(query_string)
        target_url = f"{target_url}?{query_str}"
    
    # 准备请求头 (过滤掉一些不需要转发的头)
    forward_headers = {}
    skip_headers = {'host', 'x-forwarded-for', 'x-real-ip', 'x-forwarded-proto', 
                    'x-forwarded-host', 'x-forwarded-port', 'connection'}
    
    for key, value in headers.items():
        if key.lower() not in skip_headers:
            forward_headers[key] = value
    
    # 设置 User-Agent (如果没有)
    if 'user-agent' not in [k.lower() for k in forward_headers.keys()]:
        forward_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    try:
        # 创建请求
        req = urllib.request.Request(
            target_url,
            data=body.encode('utf-8') if body and method not in ('GET', 'HEAD') else None,
            headers=forward_headers,
            method=method
        )

        # 记录请求开始时间
        start_time = time.time()

        # 发送请求
        with urllib.request.urlopen(req, timeout=25) as response:
            # HEAD 请求不读取 body
            if method == 'HEAD':
                response_body = ''
            else:
                response_body = response.read()
            response_headers = dict(response.headers)
            status_code = response.status

            # 计算耗时
            elapsed_ms = int((time.time() - start_time) * 1000)

            # 记录日志
            add_log(method, target_url, status_code, elapsed_ms)
            print(f"[代理] {method} {target_url} -> {status_code} ({elapsed_ms}ms)")

            # 尝试解码为文本 (仅非 HEAD 请求)
            if method != 'HEAD' and response_body:
                content_type = response_headers.get('Content-Type', '')
                if 'application/json' in content_type or 'text/' in content_type:
                    try:
                        response_body = response_body.decode('utf-8')
                    except:
                        import base64
                        response_body = base64.b64encode(response_body).decode('utf-8')
                        response_headers['X-Body-Encoding'] = 'base64'
                else:
                    import base64
                    response_body = base64.b64encode(response_body).decode('utf-8')
                    response_headers['X-Body-Encoding'] = 'base64'

        # 添加 CORS 头
        response_headers['Access-Control-Allow-Origin'] = '*'
        response_headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, HEAD, OPTIONS'
        response_headers['Access-Control-Allow-Headers'] = '*'

        return {
            'statusCode': status_code,
            'headers': response_headers,
            'body': response_body
        }

    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
        error_body = ''
        try:
            error_body = e.read().decode('utf-8', errors='ignore')
        except:
            pass

        # 记录日志
        add_log(method, target_url, e.code, elapsed_ms, '目标返回错误')
        print(f"[代理] {method} {target_url} -> {e.code} ({elapsed_ms}ms) [目标返回错误]")

        return {
            'statusCode': e.code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'目标服务器返回 HTTP {e.code}',
                'target_url': target_url,
                'response': error_body[:500] if error_body else ''
            }, ensure_ascii=False)
        }
    except urllib.error.URLError as e:
        elapsed_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0

        # 记录日志
        add_log(method, target_url, 502, elapsed_ms, f'连接失败: {e.reason}')
        print(f"[代理] {method} {target_url} -> 502 ({elapsed_ms}ms) [连接失败: {e.reason}]")

        return {
            'statusCode': 502,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '无法连接到目标服务器',
                'target_url': target_url,
                'reason': str(e.reason)
            }, ensure_ascii=False)
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0

        # 记录日志
        add_log(method, target_url, 500, elapsed_ms, f'内部错误: {e}')
        print(f"[代理] {method} {target_url} -> 500 ({elapsed_ms}ms) [内部错误: {e}]")

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '代理内部错误',
                'message': str(e)
            }, ensure_ascii=False)
        }

