import os
import json
from collections import defaultdict

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# 收集所有表的主键uuid
primary_keys = defaultdict(set)
# 收集所有外键引用（表名, 字段名, uuid, 来源文件, 来源行号）
foreign_keys = []

# 需要检查的外键字段名
fk_fields = ['user_id', 'role_id', 'position_id', 'dept_id', 'parent_id', 'creator_id', 'menu_id', 'dict_type', 'notice_id', 'job_id', 'config_id']

# 针对不同表补全最小字段集
DEFAULT_FIELDS = {
    'system_dept': {"name": "自动补全", "order": 1, "available": True},
    'system_position': {"name": "自动补全", "order": 1, "available": True},
    'system_role': {"name": "自动补全", "order": 1, "available": True},
    'system_menu': {"name": "自动补全", "type": 1, "order": 1, "available": True, "cache": True},
    'system_users': {"username": "autofill", "password": "autofill", "name": "自动补全", "available": True, "is_superuser": False},
    'system_dict_type': {"dict_name": "自动补全", "dict_type": "autofill", "available": True},
    'system_dict_data': {"dict_label": "自动补全", "dict_value": "autofill", "dict_type": "autofill", "available": True},
    'system_notice': {"notice_title": "自动补全", "notice_type": "1", "notice_content": "自动补全", "available": True},
    'system_job': {"name": "自动补全", "func": "autofill", "trigger": "autofill", "status": True},
    'system_config': {"config_name": "自动补全", "config_key": "autofill", "config_value": "autofill", "config_type": True},
}

# 1. 读取所有json，收集主键和外键
json_data = {}
for filename in os.listdir(DATA_DIR):
    if filename.endswith('.json'):
        table = filename.replace('.json', '')
        with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"文件 {filename} 解析失败: {e}")
                continue
            if not isinstance(data, list):
                continue
            json_data[table] = data
            for idx, row in enumerate(data):
                # 收集主键
                if 'id' in row and isinstance(row['id'], str):
                    primary_keys[table].add(row['id'])
                # 收集外键
                for fk in fk_fields:
                    if fk in row and isinstance(row[fk], str) and row[fk]:
                        foreign_keys.append((fk, row[fk], table, filename, idx+1))

# 2. 检查外键引用，补充主表缺失uuid
add_count = 0
for fk, uuid_val, table, filename, lineno in foreign_keys:
    if fk.endswith('_id'):
        main_table = fk.replace('_id', '')
        # 特殊处理dict_type等
        if main_table == 'dict_type':
            main_table = 'system_dict_type'
        elif main_table == 'parent':
            main_table = table
        elif main_table == 'menu':
            main_table = 'system_menu'
        elif main_table == 'notice':
            main_table = 'system_notice'
        elif main_table == 'job':
            main_table = 'system_job'
        elif main_table == 'config':
            main_table = 'system_config'
        elif main_table == 'user':
            main_table = 'system_users'
        elif main_table == 'role':
            main_table = 'system_role'
        elif main_table == 'position':
            main_table = 'system_position'
        elif main_table == 'dept':
            main_table = 'system_dept'
        # 如果主表没有该uuid，补充一条空白记录并补全NOT NULL字段
        if uuid_val not in primary_keys.get(main_table, set()):
            print(f"为 {main_table}.json 补充缺失id: {uuid_val}")
            record = {"id": uuid_val}
            record.update(DEFAULT_FIELDS.get(main_table, {}))
            json_data.setdefault(main_table, []).append(record)
            primary_keys[main_table].add(uuid_val)
            add_count += 1

# 强制补全 system_dept.json 所有记录的 name/order/available 字段
for row in json_data.get('system_dept', []):
    if not row.get('name'):
        row['name'] = '自动补全'
    if 'order' not in row:
        row['order'] = 1
    if 'available' not in row:
        row['available'] = True

# 强制将所有 system_users 的 dept_id 设为顶级部门
if 'system_users' in json_data and 'system_dept' in json_data:
    # 找到顶级部门id
    top_dept_id = None
    for row in json_data['system_dept']:
        if row.get('parent_id') is None:
            top_dept_id = row['id']
            break
    for row in json_data['system_users']:
        row['dept_id'] = top_dept_id

# 3. 保存所有被修改的json文件
for table, data in json_data.items():
    file_path = os.path.join(DATA_DIR, f"{table}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print(f"已自动修复 {add_count} 个外键引用，所有json文件已更新！") 