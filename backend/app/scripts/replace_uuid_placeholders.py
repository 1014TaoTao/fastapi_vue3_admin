import uuid
import os
import re

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
uuid_map = {}

# 1. 先扫描所有json文件，收集所有{uuid-xxx}占位符
for filename in os.listdir(DATA_DIR):
    if filename.endswith('.json'):
        with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
            content = f.read()
            for match in re.findall(r'\{uuid-[^}]+\}', content):
                if match not in uuid_map:
                    uuid_map[match] = str(uuid.uuid4())

# 2. 替换所有json文件中的占位符为真实uuid
for filename in os.listdir(DATA_DIR):
    if filename.endswith('.json'):
        file_path = os.path.join(DATA_DIR, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for k, v in uuid_map.items():
            content = content.replace(k, v)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

print(f"已替换 {len(uuid_map)} 个UUID占位符，所有json文件已更新！") 