import os
import json
import uuid
import shutil
from pathlib import Path

# 需要处理的依赖字段
ID_FIELDS = [
    'id', 'parent_id', 'role_id', 'user_id', 'dept_id', 'menu_id', 'position_id', 'job_id',
    'notice_id', 'dict_id', 'dict_type_id', 'config_id', 'creator_id', 'updater_id', 'operation_log_id'
]

DATA_DIR = Path(__file__).parent / 'data'

# 1. 收集所有 id
id_map = {}

# 记录每个文件中所有出现的 id
file_id_fields = {}

# 先扫描所有文件，收集所有 id
for filename in os.listdir(DATA_DIR):
    if not filename.endswith('.json'):
        continue
    filepath = DATA_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"读取 {filename} 失败: {e}")
            continue
    ids_in_file = set()
    def collect_ids(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ID_FIELDS and v is not None:
                    ids_in_file.add(str(v))
                collect_ids(v)
        elif isinstance(obj, list):
            for item in obj:
                collect_ids(item)
    collect_ids(data)
    file_id_fields[filename] = ids_in_file
    for _id in ids_in_file:
        if _id not in id_map:
            id_map[_id] = str(uuid.uuid4())

# 2. 替换所有 id 及依赖字段
for filename in os.listdir(DATA_DIR):
    if not filename.endswith('.json'):
        continue
    filepath = DATA_DIR / filename
    # 备份原文件
    shutil.copy(filepath, str(filepath) + '.bak')
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    def replace_ids(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ID_FIELDS and v is not None:
                    v_str = str(v)
                    if v_str in id_map:
                        obj[k] = id_map[v_str]
                replace_ids(v)
        elif isinstance(obj, list):
            for item in obj:
                replace_ids(item)
    replace_ids(data)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已处理: {filename}")

print("所有 JSON 文件已完成 UUID 替换，原文件已备份为 .bak") 