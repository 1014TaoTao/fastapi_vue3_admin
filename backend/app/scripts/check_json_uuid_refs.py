import os
import json
from collections import defaultdict

data_dir = os.path.join(os.path.dirname(__file__), 'data')

# 收集所有表的主键uuid
primary_keys = defaultdict(set)
# 收集所有外键引用（表名, 字段名, uuid, 来源文件, 来源行号）
foreign_keys = []

# 需要检查的外键字段名
fk_fields = ['user_id', 'role_id', 'position_id', 'dept_id', 'parent_id', 'creator_id', 'menu_id', 'dict_type', 'notice_id', 'job_id', 'config_id']

for filename in os.listdir(data_dir):
    if filename.endswith('.json'):
        table = filename.replace('.json', '')
        with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"文件 {filename} 解析失败: {e}")
                continue
            if not isinstance(data, list):
                continue
            for idx, row in enumerate(data):
                # 收集主键
                if 'id' in row and isinstance(row['id'], str):
                    primary_keys[table].add(row['id'])
                # 收集外键
                for fk in fk_fields:
                    if fk in row and isinstance(row[fk], str) and row[fk]:
                        foreign_keys.append((fk, row[fk], table, filename, idx+1))

# 检查外键引用
print('检查外键引用关系...')
not_found = []
for fk, uuid_val, table, filename, lineno in foreign_keys:
    # 推测主表名
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
        if uuid_val not in primary_keys.get(main_table, set()):
            not_found.append((filename, lineno, fk, uuid_val, main_table))

if not_found:
    print('未匹配的外键引用:')
    for filename, lineno, fk, uuid_val, main_table in not_found:
        print(f"文件 {filename} 第{lineno}行 字段 {fk} 引用 {main_table} 中不存在的id: {uuid_val}")
else:
    print('所有外键引用均已正确匹配！') 