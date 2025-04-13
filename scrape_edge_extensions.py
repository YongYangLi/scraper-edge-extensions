# -*- coding: utf-8 -*-
import requests
import xml.etree.ElementTree as ET
import json
import re
import sqlite3

# 从网络获取sitemap.xml
sitemap_url = 'https://microsoftedge.microsoft.com/sitemap.xml'
response = requests.get(sitemap_url)
response.raise_for_status()

# 解析XML内容
root = ET.fromstring(response.content)

# 提取所有<loc>标签中的URL
urls = [url.text for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]

# 存储所有扩展信息的列表
extensions_data = []

# 对每个URL提取ID并构造API请求
for url in urls:
    try:
        print(f"正在处理: {url}")
        # 从URL中提取ID
        match = re.search(r'detail/([^/]+)', url)
        if not match:
            print(f"URL格式不匹配，跳过: {url}")
            continue
        ext_id = match.group(1)
        
        # 构造API请求URL
        api_url = f"https://microsoftedge.microsoft.com/addons/getproductdetailsbycrxid/{ext_id}?hl=zh-CN&gl=CN"
        
        # 发送API请求
        response = requests.get(api_url)
        if response.status_code == 200:
            ext_data = {
                'url': url,
                'api_url': api_url,
                'data': response.json()
            }
            extensions_data.append(ext_data)
            print(f"成功处理: {url}")
        else:
            print(f"处理失败: {url}, 状态码: {response.status_code}")
    except Exception as e:
        print(f"处理错误: {url}: {e}")

# 将结果保存为JSON文件
with open('edge_extensions_data.json', 'w', encoding='utf-8') as f:
    json.dump(extensions_data, f, ensure_ascii=False, indent=2)

print(f"成功保存{len(extensions_data)}个扩展数据到edge_extensions_data.json".encode('utf-8').decode('utf-8'))

# 创建SQLite数据库和表
def create_database():
    conn = sqlite3.connect('edge_extensions.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS extensions (
                      url TEXT PRIMARY KEY,
                      activeInstallCount INTEGER,
                      storeProductId TEXT,
                      name TEXT,
                      logoUrl TEXT,
                      thumbnailUrl TEXT,
                      description TEXT,
                      developer TEXT,
                      category TEXT,
                      isInstalled BOOLEAN,
                      crxId TEXT,
                      version TEXT,
                      lastUpdateDate REAL,
                      privacyUrl TEXT,
                      averageRating REAL,
                      ratingCount INTEGER
                    )''')
    
    conn.commit()
    return conn

# 将数据导入数据库
def import_to_database(conn, extensions_data):
    cursor = conn.cursor()
    
    for ext in extensions_data:
        data = ext['data']
        cursor.execute('''INSERT OR REPLACE INTO extensions VALUES (
                          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )''', (
                            ext['url'],
                            data['activeInstallCount'],
                            data['storeProductId'],
                            data['name'],
                            data['logoUrl'],
                            data['thumbnailUrl'],
                            data['description'],
                            data['developer'],
                            data['category'],
                            data['isInstalled'],
                            data['crxId'],
                            data['version'],
                            data['lastUpdateDate'],
                            data['privacyUrl'],
                            data['averageRating'],
                            data['ratingCount']
                        ))
    
    conn.commit()

if __name__ == '__main__':
    # 执行爬取并保存到JSON
    # 创建数据库连接
    conn = create_database()
    # 将数据导入数据库
    import_to_database(conn, extensions_data)
    conn.close()
    print("数据已成功导入SQLite数据库")