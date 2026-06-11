"""
验证 Inta-mart API 调用方案 D：
后端 Python 用 cookie 获取页面 → 提取 session token → 调 API → 解析数据

用法：
1. 在浏览器打开 https://stg.azure-pilot.aida.ajis-group.com/imart/ajis/FP9908-1?
2. F12 → Network → 找到任意一个请求 → Request Headers → 复制 Cookie 的完整值
   (注意：不能用 document.cookie，因为它不包含 HttpOnly 的 JSESSIONID)
3. 运行: python tests/verify_intamart_api.py "完整Cookie字符串"
"""

import re
import sys
import json
import html

BASE_URL = "https://stg.azure-pilot.aida.ajis-group.com"
PAGE_PATH = "/imart/ajis/FP9908-1?"  # 社員マスター


def hex_decode(hex_str: str) -> str:
    """解码 Inta-mart 的 hex 编码属性名（如 \\63\\6F\\6C\\31 → col1）"""
    result = []
    i = 0
    while i < len(hex_str):
        if hex_str[i] == '\\' and i + 2 < len(hex_str):
            try:
                code = int(hex_str[i + 1:i + 3], 16)
                result.append(chr(code))
                i += 3
                continue
            except (ValueError, IndexError):
                pass
        result.append(hex_str[i])
        i += 1
    return ''.join(result)


def parse_jsxml(xml_text: str) -> dict:
    """
    简单解析 Inta-mart 的 JSXML 格式。
    JSXML 格式:
      <object>...</object>
      <array name="xxx">...</array>
      <string name="xxx" value="yyy"/>
      <number name="xxx" value="123"/>
      <null name="xxx"/>
    """
    # 移除 XML 声明
    xml_text = xml_text.strip()
    
    def parse_node(pos: int) -> tuple[dict, int]:
        """递归解析一个节点，返回 (parsed_value, new_pos)"""
        # 跳过空白
        while pos < len(xml_text) and xml_text[pos] in ' \t\n\r':
            pos += 1
        if pos >= len(xml_text):
            return None, pos
        
        # 找到标签
        if xml_text[pos] != '<':
            raise ValueError(f"Expected '<' at pos {pos}, got: {xml_text[pos:pos+20]}")
        
        tag_end = xml_text.index('>', pos)
        tag_content = xml_text[pos + 1:tag_end]
        
        # 判断标签类型
        if 'null' in tag_content:
            name = re.search(r'name="([^"]*)"', tag_content)
            name_val = hex_decode(name.group(1)) if name else None
            return {name_val: None} if name_val else None, tag_end + 1
        
        elif 'number' in tag_content:
            name = re.search(r'name="([^"]*)"', tag_content)
            value = re.search(r'value="([^"]*)"', tag_content)
            name_val = hex_decode(name.group(1)) if name else None
            value_val = float(value.group(1)) if value else 0
            result = {name_val: value_val} if name_val else value_val
            # Check for self-closing />
            return result, tag_end + 1
        
        elif 'string' in tag_content:
            name = re.search(r'name="([^"]*)"', tag_content)
            value = re.search(r'value="([^"]*)"', tag_content)
            name_val = hex_decode(name.group(1)) if name else None
            value_val = hex_decode(value.group(1)) if value else ''
            # unescape HTML entities like &#32;
            value_val = html.unescape(value_val)
            result = {name_val: value_val} if name_val else value_val
            return result, tag_end + 1
        
        elif 'object' in tag_content:
            name = re.search(r'name="([^"]*)"', tag_content)
            name_val = hex_decode(name.group(1)) if name else None
            obj = {}
            close_tag = f'</object>'
            pos = tag_end + 1
            while pos < len(xml_text):
                if xml_text[pos:pos + len(close_tag)] == close_tag:
                    pos += len(close_tag)
                    break
                child, pos = parse_node(pos)
                if child and isinstance(child, dict):
                    obj.update(child)
            return ({name_val: obj} if name_val else obj), pos
        
        elif 'array' in tag_content:
            name = re.search(r'name="([^"]*)"', tag_content)
            name_val = hex_decode(name.group(1)) if name else None
            arr = []
            close_tag = f'</array>'
            pos = tag_end + 1
            while pos < len(xml_text):
                if xml_text[pos:pos + len(close_tag)] == close_tag:
                    pos += len(close_tag)
                    break
                child, pos = parse_node(pos)
                if child is not None:
                    arr.append(child)
            return ({name_val: arr} if name_val else arr), pos
        
        else:
            # Unknown or self-closing tag, skip
            return None, tag_end + 1
    
    result, _ = parse_node(0)
    return result


def extract_token_from_html(html_text: str) -> str | None:
    """从 Inta-mart 页面 HTML 中提取 listtable session token"""
    # 匹配 "url":"component-ajax-service\/listtable\/session\/XXXXX"
    match = re.search(r'"url"\s*:\s*"component-ajax-service\\?/listtable\\?/session\\?/([a-f0-9]+)"', html_text)
    if match:
        token = match.group(1)
        return token
    return None


def parse_cookie_string(cookie_str: str) -> dict:
    """将 'key1=val1; key2=val2' 格式的字符串解析为 dict"""
    cookies = {}
    for part in cookie_str.split(';'):
        part = part.strip()
        if '=' in part:
            key, val = part.split('=', 1)
            cookies[key.strip()] = val.strip()
    return cookies


def main():
    if len(sys.argv) < 2:
        print("用法: python tests/verify_intamart_api.py \"<完整Cookie字符串>\"")
        print()
        print("获取 Cookie：")
        print("  1. 浏览器打开目标页面")
        print("  2. F12 → Network → 找任意请求 → Request Headers → 复制 Cookie 全部")
        print("     (不能用 document.cookie，不含 HttpOnly 的 JSESSIONID)")
        sys.exit(1)
    
    cookie_header = sys.argv[1]  # 直接用原始字符串，不解析重建
    
    print(f"📋 Cookie 长度: {len(cookie_header)} 字符")
    # 找 JSESSIONID
    for part in cookie_header.split(';'):
        if 'JSESSIONID' in part:
            print(f"     {part.strip()[:60]}")
    
    # 使用 urllib（无需额外安装）
    import ssl
    import urllib.request
    
    # 创建不验证 SSL 的 context（staging 环境）
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # ========== 步骤 1: 访问目标页面，提取 session token ==========
    print(f"\n{'='*60}")
    print(f"🔍 步骤 1: 获取页面 {PAGE_PATH}")
    print(f"{'='*60}")
    
    page_url = f"{BASE_URL}{PAGE_PATH}"
    req = urllib.request.Request(page_url, headers={
        'Cookie': cookie_header,
        'User-Agent': 'Mozilla/5.0 (Python IntaMart Client)'
    })
    
    try:
        resp = urllib.request.urlopen(req, context=ctx)
        html_text = resp.read().decode('utf-8', errors='replace')
        print(f"✅ 页面获取成功: {resp.status}, 大小: {len(html_text)} bytes")
    except Exception as e:
        print(f"❌ 页面获取失败: {e}")
        sys.exit(1)
    
    token = extract_token_from_html(html_text)
    if not token:
        print("❌ 未找到 session token！")
        print("   可能原因: 1. Cookie 已过期  2. 页面结构变了")
        print(f"\n页面片段（前 500 字符）:\n{html_text[:500]}")
        sys.exit(1)
    
    print(f"✅ 找到 session token: {token}")
    
    # ========== 步骤 2: 用 token 调用 listtable API ==========
    print(f"\n{'='*60}")
    print(f"🔍 步骤 2: 调用 listtable API")
    print(f"{'='*60}")
    
    api_path = f"/imart/component-ajax-service/listtable/session/{token}"
    api_url = f"{BASE_URL}{api_path}"
    
    # 构建请求体（与 Inta-mart 页面相同的 JSXML 格式）
    xml_body = (
        '<object>'
        '<number name="\\70\\61\\67\\65" value="1"/>'      # page=1
        '<number name="\\72\\6f\\77\\4e\\75\\6d" value="10"/>'  # rowNum=10
        '<string name="\\73\\6f\\72\\74\\49\\6e\\64\\65\\78" value=""/>'  # sortIndex=""
        '<string name="\\73\\6f\\72\\74\\4f\\72\\64\\65\\72" value="\\61\\73\\63"/>'  # sortOrder=asc
        '<object name="\\65\\78\\74\\65\\6e\\73\\69\\6f\\6e">'  # extension
        '<string name="\\75\\73\\65\\72\\43\\6f\\64\\65" value=""/>'  # userCode
        '<string name="\\75\\73\\65\\72\\4e\\61\\6d\\65" value=""/>'  # userName
        '<string name="\\75\\73\\65\\72\\4e\\61\\6d\\65\\4b\\61\\6e\\61" value=""/>'  # userNameKana
        '<string name="\\64\\75\\74\\79" value=""/>'  # duty
        '<string name="\\6f\\72\\67\\31" value="\\30\\30\\31"/>'  # org1=001
        '<string name="\\6f\\72\\67\\32" value="\\30\\31\\30\\32\\30\\30\\30\\34"/>'  # org2=01020004
        '<string name="\\72\\65\\74\\69\\72\\65\\53\\74\\61\\74\\75\\73" value=""/>'  # retireStatus
        '</object>'
        '</object>'
    )
    
    req2 = urllib.request.Request(api_url, data=xml_body.encode('utf-8'), headers={
        'Cookie': cookie_header,
        'Content-Type': 'application/xml',
        'X-Requested-With': 'XMLHttpRequest',
        'x-jp-co-intra-mart-ajax-request-from-imui-form-util': 'false',
        'User-Agent': 'Mozilla/5.0 (Python IntaMart Client)'
    })
    
    try:
        resp2 = urllib.request.urlopen(req2, context=ctx)
        xml_response = resp2.read().decode('utf-8', errors='replace')
        print(f"✅ API 调用成功: {resp2.status}, 大小: {len(xml_response)} bytes")
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        sys.exit(1)
    
    # ========== 步骤 3: 解析响应 ==========
    print(f"\n{'='*60}")
    print(f"📊 步骤 3: 解析响应数据")
    print(f"{'='*60}")
    
    try:
        data = parse_jsxml(xml_response)
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        print(f"\n原始响应（前 1000 字符）:\n{xml_response[:1000]}")
        sys.exit(1)
    
    # 显示结构
    print(f"\n📦 响应顶层结构（解码后）:")
    print(json.dumps({k: type(v).__name__ for k, v in data.items()}, indent=2, ensure_ascii=False))
    
    total = data.get('total', 'N/A')
    data_array = data.get('data', [])
    print(f"\n📊 总记录数: {total}")
    print(f"📊 当前页记录数: {len(data_array)}")
    
    # 显示第一条记录的所有字段
    if data_array:
        print(f"\n{'='*60}")
        print(f"🔑 字段名（col1 ~ colN） 及 第一条数据:")
        print(f"{'='*60}")
        first_row = data_array[0]
        if isinstance(first_row, dict):
            # 按 key 排序显示
            for key in sorted(first_row.keys()):
                val = first_row[key]
                if isinstance(val, str):
                    display_val = val[:60]
                else:
                    display_val = str(val)[:60]
                print(f"  {key:12s} = {display_val}")
        
        # 显示对应关系
        print(f"\n{'='*60}")
        print(f"📋 前 3 条记录预览:")
        print(f"{'='*60}")
        for i, row in enumerate(data_array[:3]):
            if isinstance(row, dict):
                print(f"\n--- 记录 {i+1} ---")
                cols = sorted(row.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
                for col in cols:
                    val = row[col]
                    if isinstance(val, str) and len(val) > 50:
                        val = val[:50] + '...'
                    print(f"  {col}: {val}")
    
    # 显示完整的列名映射
    if data_array:
        print(f"\n{'='*60}")
        print(f"📋 所有字段名列表:")
        print(f"{'='*60}")
        all_keys = set()
        for row in data_array:
            if isinstance(row, dict):
                all_keys.update(row.keys())
        sorted_keys = sorted(all_keys, key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
        print(json.dumps(sorted_keys, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
