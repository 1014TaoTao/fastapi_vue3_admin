"""工作流模块（存储与文件流转）：

- ``source``: 存储源管理（OSS/COS/OBS/S3/SFTP/FTP 等连接配置）
- ``core``: 对象存储协议适配器与工厂
- ``storage``: 存储文件浏览
- ``transfer``: 传输任务引擎
- ``flow``: 工作流定义（画布 CRUD、发布、执行 API）

路由统一挂在 ``/workflow`` 下（见 ``app/api/v1/workflow.py``）。
"""
