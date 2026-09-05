import asyncio
from collections.abc import Sequence

from sqlalchemy import Inspector, inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.setting import settings
from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema
from app.core.database import engine
from app.core.logger import logger

from .model import GenTableColumnModel, GenTableModel
from .schema import (
    GenDBTableSchema,
    GenTableColumnSchema,
    GenTableSchema,
)


class GenTableCRUD(CRUDBase[GenTableModel, GenTableSchema, GenTableSchema]):
    """代码生成业务表模块数据库操作层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        """初始化CRUD操作层

        参数:
        - auth (AuthSchema): 认证信息模型
        - db (AsyncSession): 数据库会话
        """
        super().__init__(model=GenTableModel, auth=auth, db=db)

    async def get_gen_table_by_id(self, table_id: int, preload: list | None = None) -> GenTableModel | None:
        """根据业务表ID获取需要生成的业务表信息。

        参数:
        - table_id (int): 业务表ID。
        - preload (list | None): 预加载关系，未提供时使用模型默认项

        返回:
        - GenTableModel | None: 业务表信息对象。
        """
        return await self.get(id=table_id, preload=preload)

    async def get_gen_table_by_name(self, table_name: str, preload: list | None = None) -> GenTableModel | None:
        """根据业务表名称获取需要生成的业务表信息。

        参数:
        - table_name (str): 业务表名称。
        - preload (list | None): 预加载关系，未提供时使用模型默认项

        返回:
        - GenTableModel | None: 业务表信息对象。
        """
        return await self.get(table_name=table_name, preload=preload)

    async def add_gen_table(self, add_model: GenTableSchema) -> GenTableModel:
        """新增业务表信息。

        参数:
        - add_model (GenTableSchema): 新增业务表信息模型。

        返回:
        - GenTableModel: 新增的业务表信息对象。
        """
        return await self.create(data=add_model)

    async def edit_gen_table(self, table_id: int, edit_model: GenTableSchema) -> GenTableModel:
        """修改业务表信息。

        参数:
        - table_id (int): 业务表ID。
        - edit_model (GenTableSchema): 修改业务表信息模型。

        返回:
        - GenTableSchema: 修改后的业务表信息模型。
        """
        # 排除嵌套对象字段，避免SQLAlchemy尝试直接将字典设置到模型实例上
        return await self.update(
            id=table_id,
            data=GenTableSchema(**edit_model.model_dump(exclude_unset=True, exclude={"columns"})),
        )

    async def delete_gen_table(self, ids: list[int]) -> None:
        """删除业务表信息。除了系统表。

        参数:
        - ids (list[int]): 业务表ID列表。

        返回:
        - None
        """
        await self.delete(ids=ids)

    async def get_db_table_list(self, table_name: str | None = None, table_comment: str | None = None) -> list[dict]:
        """根据查询参数获取数据库表列表信息。

        参数:
        - table_name (str | None): 表名关键字（模糊匹配）。
        - table_comment (str | None): 表注释关键字（模糊匹配）。

        返回:
        - list[dict]: 数据库表列表信息（已转为可序列化字典）。
        """
        # Inspector 基于同步引擎，在线程池中执行避免阻塞事件循环
        return await asyncio.to_thread(self._sync_get_db_table_list, table_name, table_comment)

    @staticmethod
    def _sync_get_db_table_list(table_name: str | None, table_comment: str | None) -> list[dict]:
        """同步实现：遍历 Inspector 获取数据库表列表（仅在线程池中调用）。"""
        database_name = settings.DATABASE_NAME
        database_type = settings.DATABASE_TYPE

        inspector: Inspector = inspect(engine)
        table_names = inspector.get_table_names()

        name_kw = table_name.strip() if table_name else ""
        comment_kw = table_comment.strip() if table_comment else ""

        dict_data = []
        for physical_name in table_names:
            try:
                comment_info = inspector.get_table_comment(physical_name)
                comment = comment_info.get("text", "") if isinstance(comment_info, dict) else comment_info
                physical_comment = comment or ""
            except Exception as e:
                logger.warning(f"获取表 {physical_name} 的注释失败: {e}")
                physical_comment = ""

            # 表名过滤：忽略大小写，支持模糊匹配
            if name_kw and name_kw.lower() not in physical_name.lower():
                continue
            # 表注释过滤：忽略大小写，支持模糊匹配；注释为 None 时视为空字符串
            if comment_kw and comment_kw not in physical_comment:
                continue

            dict_data.append(
                GenDBTableSchema(
                    database_name=database_name,
                    table_name=physical_name,
                    table_type=database_type,
                    table_comment=physical_comment,
                ).model_dump(),
            )

        return dict_data

    async def get_db_table_page(
        self,
        table_name: str | None = None,
        table_comment: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[dict], int]:
        """数据库侧分页获取物理表列表（用于导入表弹窗）。

        说明：
        - 旧实现使用 SQLAlchemy Inspector 全量遍历再内存分页，表多时非常慢。
        - 这里按方言走系统表（MySQL information_schema / Postgres pg_catalog）进行分页与过滤。
        - 若方言不支持，则回退到旧的全量遍历。

        参数:
        - table_name (str | None): 表名关键字（模糊匹配）。
        - table_comment (str | None): 表注释关键字（模糊匹配）。
        - offset (int): 偏移量。
        - limit (int): 每页条数。

        返回:
        - tuple[list[dict], int]: 当前页表信息列表与总条数。
        """
        database_name = settings.DATABASE_NAME
        db_type = (settings.DATABASE_TYPE or "").lower()

        name_kw = table_name.strip() if table_name else None
        comment_kw = table_comment.strip() if table_comment else None

        # MySQL / MariaDB
        if db_type in {"mysql", "mariadb"}:
            where_sql = "WHERE table_schema = :db AND table_type = 'BASE TABLE'"
            params: dict = {"db": database_name, "offset": offset, "limit": limit}
            if name_kw:
                where_sql += " AND table_name LIKE :name_kw"
                params["name_kw"] = f"%{name_kw}%"
            if comment_kw:
                where_sql += " AND table_comment LIKE :comment_kw"
                params["comment_kw"] = f"%{comment_kw}%"

            count_sql = text(f"SELECT COUNT(1) AS cnt FROM information_schema.tables {where_sql}")
            rows_sql = text(f"SELECT table_name, table_comment FROM information_schema.tables {where_sql} ORDER BY table_name ASC LIMIT :limit OFFSET :offset")
            total_res = await self.db.execute(count_sql, params)
            total = int(total_res.scalar() or 0)
            res = await self.db.execute(rows_sql, params)
            items: list[dict] = []
            for r in res.fetchall():
                # r may be Row/tuple depending on driver
                table_name = r[0]
                table_comment = r[1] or ""
                items.append(
                    GenDBTableSchema(
                        database_name=database_name,
                        table_name=table_name,
                        table_type=settings.DATABASE_TYPE,
                        table_comment=table_comment,
                    ).model_dump(),
                )
            return items, total

        # PostgreSQL
        if db_type in {"postgresql", "postgres"}:
            # pg_description 需要通过 objsubid=0 获取 table comment
            where_sql = "WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND c.relkind = 'r'"
            params = {"offset": offset, "limit": limit}
            if name_kw:
                where_sql += " AND c.relname ILIKE :name_kw"
                params["name_kw"] = f"%{name_kw}%"
            if comment_kw:
                where_sql += " AND COALESCE(d.description,'') ILIKE :comment_kw"
                params["comment_kw"] = f"%{comment_kw}%"

            base_from = "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace LEFT JOIN pg_catalog.pg_description d ON d.objoid = c.oid AND d.objsubid = 0 "
            count_sql = text(f"SELECT COUNT(1) AS cnt {base_from} {where_sql}")
            rows_sql = text(f"SELECT c.relname AS table_name, COALESCE(d.description,'') AS table_comment {base_from} {where_sql} ORDER BY c.relname ASC LIMIT :limit OFFSET :offset")
            total_res = await self.db.execute(count_sql, params)
            total = int(total_res.scalar() or 0)
            res = await self.db.execute(rows_sql, params)
            items = []
            for r in res.fetchall():
                table_name = r[0]
                table_comment = r[1] or ""
                items.append(
                    GenDBTableSchema(
                        database_name=database_name,
                        table_name=table_name,
                        table_type=settings.DATABASE_TYPE,
                        table_comment=table_comment,
                    ).model_dump(),
                )
            return items, total

        # Fallback：回退旧逻辑（全量遍历再分页由上层处理）
        all_items = await self.get_db_table_list(table_name=name_kw, table_comment=comment_kw)
        total = len(all_items)
        return all_items[offset : offset + limit], total

    async def get_db_table_list_by_names(self, table_names: list[str]) -> list[GenDBTableSchema]:
        """根据业务表名称列表获取数据库表信息。

        参数:
        - table_names (list[str]): 业务表名称列表。

        返回:
        - list[GenDBTableSchema]: 数据库表信息对象列表。
        """
        if not table_names:
            return []
        # Inspector 基于同步引擎，在线程池中执行避免阻塞事件循环
        return await asyncio.to_thread(self._sync_get_db_table_list_by_names, table_names)

    @staticmethod
    def _sync_get_db_table_list_by_names(table_names: list[str]) -> list[GenDBTableSchema]:
        """同步实现：按表名列表获取数据库表信息（仅在线程池中调用）。"""
        database_name = settings.DATABASE_NAME
        database_type = settings.DATABASE_TYPE

        inspector: Inspector = inspect(engine)
        all_table_names = set(inspector.get_table_names())

        results = []
        for table_name in table_names:
            if table_name not in all_table_names:
                continue
            try:
                table_comment = inspector.get_table_comment(table_name)
                comment = table_comment.get("text", "") if isinstance(table_comment, dict) else (table_comment or "")
            except Exception as e:
                logger.warning(f"获取表 {table_name} 的注释失败: {e}")
                comment = ""

            results.append(
                GenDBTableSchema(
                    database_name=database_name,
                    table_name=table_name,
                    table_type=database_type,
                    table_comment=comment or "",
                ),
            )

        return results

    async def check_table_exists(self, table_name: str) -> bool:
        """检查数据库中是否已存在指定表名的表。

        参数:
        - table_name (str): 要检查的表名。

        返回:
        - bool: 如果表存在返回True，否则返回False。
        """
        return await asyncio.to_thread(self._sync_check_table_exists, table_name)

    @staticmethod
    def _sync_check_table_exists(table_name: str) -> bool:
        """同步实现：检查表是否存在（仅在线程池中调用）。"""
        return inspect(engine).has_table(table_name)

    async def get_db_table_comment(self, table_name: str) -> str:
        """获取数据库中指定表的注释（用于主子表场景下从库中加载子表元信息）。

        参数:
        - table_name (str): 物理表名。

        返回:
        - str: 表注释；表不存在或失败时为空字符串。
        """
        return await asyncio.to_thread(self._sync_get_db_table_comment, table_name)

    @staticmethod
    def _sync_get_db_table_comment(table_name: str) -> str:
        """同步实现：获取表注释（仅在线程池中调用）。"""
        inspector: Inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return ""
        try:
            table_comment = inspector.get_table_comment(table_name)
            comment = table_comment.get("text", "") if isinstance(table_comment, dict) else (table_comment or "")
            return comment or ""
        except Exception as e:
            logger.warning(f"获取表 {table_name} 的注释失败: {e}")
            return ""

    async def execute_sql(self, sql: str) -> bool:
        """执行SQL语句。

        参数:
        - sql (str): 要执行的SQL语句。

        返回:
        - bool: 是否执行成功。
        """
        try:
            # 执行SQL但不手动提交事务，由框架管理事务生命周期
            await self.db.execute(text(sql))
            return True
        except Exception as e:
            logger.error(f"执行SQL时发生错误: {e}")
            return False


class GenTableColumnCRUD(CRUDBase[GenTableColumnModel, GenTableColumnSchema, GenTableColumnSchema]):
    """代码生成业务表字段模块数据库操作层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        """初始化CRUD操作层

        参数:
        - auth (AuthSchema): 认证信息模型
        - db (AsyncSession): 数据库会话
        """
        super().__init__(model=GenTableColumnModel, auth=auth, db=db)

    @staticmethod
    def _sync_get_table_columns(database_type: str, table_name: str) -> list[dict]:
        """同步函数：获取数据库表的列信息

        参数:
        - database_type: 数据库类型
        - table_name: 表名

        返回:
        - list: 列信息列表
        """
        # 使用SQLAlchemy Inspector获取表列信息
        inspector: Inspector = inspect(engine)

        # 获取列信息
        columns = inspector.get_columns(table_name)

        # 获取主键信息
        try:
            pk_constraint = inspector.get_pk_constraint(table_name)
            primary_keys = set(pk_constraint.get("constrained_columns", [])) if pk_constraint else set()
        except Exception:
            primary_keys = set()

        # 获取唯一约束信息
        unique_columns = set()
        unique_constraints = inspector.get_unique_constraints(table_name)
        for constraint in unique_constraints:
            unique_columns.update(constraint.get("column_names", []))

        # 处理列信息
        columns_list = []
        for idx, column in enumerate(columns):
            # 获取列的基本信息
            column_name = column["name"]
            column_type = str(column["type"])
            is_nullable = column.get("nullable", True)
            column_default = column.get("default", None)
            # 获取列注释（如果有的话）
            column_comment = column.get("comment", "")
            # 判断是否为主键
            is_pk = column_name in primary_keys
            # 判断是否为唯一约束
            is_unique = column_name in unique_columns
            # 判断是否为自增列（基于数据库类型和列类型）
            is_increment = column.get("autoincrement", False) in (True, "auto")
            # 获取列长度（如果适用）
            col_len = getattr(column["type"], "length", None)
            column_length = str(col_len) if col_len is not None else ""

            # 构造列信息字典
            column_info = {
                "column_name": column_name,
                "column_comment": column_comment or "",
                "column_type": column_type,
                "column_length": column_length or "",
                "column_default": str(column_default) if column_default is not None else "",
                "sort": idx + 1,  # 序号从1开始
                "is_pk": bool(is_pk),
                "is_increment": bool(is_increment),
                "is_nullable": bool(is_nullable),
                "is_unique": bool(is_unique),
            }

            columns_list.append(column_info)

        return columns_list

    async def get_gen_table_column_by_id(self, id: int, preload: list | None = None) -> GenTableColumnModel | None:
        """根据业务表字段ID获取业务表字段信息。

        参数:
        - id (int): 业务表字段ID。
        - preload (list | None): 预加载关系，未提供时使用模型默认项

        返回:
        - GenTableColumnModel | None: 业务表字段信息对象。
        """
        return await self.get(id=id, preload=preload)

    async def list_gen_table_column_crud_by_table_id(
        self,
        table_id: int,
        order_by: list | None = None,
        preload: list | None = None,
    ) -> Sequence[GenTableColumnModel]:
        """根据业务表ID查询业务表字段列表。

        参数:
        - table_id (int): 业务表ID。
        - order_by (list | None): 排序字段列表，每个元素为{"field": "字段名", "order": "asc" | "desc"}。
        - preload (list | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[GenTableColumnModel]: 业务表字段列表信息对象序列。
        """
        return await self.get_list(search={"table_id": table_id}, order_by=order_by, preload=preload)

    async def get_gen_db_table_columns_by_name(self, table_name: str | None) -> list[dict]:
        """获取物理数据库表的列信息（原始字典）。

        说明:
        - 仅返回 DB 元信息的原生字典，模型转换（OutSchema）由 Service 层完成。

        参数:
        - table_name (str | None): 物理表名称。

        返回:
        - list[dict]: 列信息字典列表。
        """
        # 检查表名是否为空
        if not table_name:
            raise ValueError("数据表名称不能为空")

        try:
            # 在线程池中执行同步 inspect 操作，避免阻塞事件循环
            return await asyncio.to_thread(
                GenTableColumnCRUD._sync_get_table_columns,
                settings.DATABASE_TYPE,
                table_name,
            )
        except Exception as e:
            logger.error(f"获取表{table_name}的字段列表时出错: {e!s}")
            raise

    async def list_gen_table_column_crud(
        self,
        search: dict | None = None,
        order_by: list | None = None,
        preload: list | None = None,
    ) -> Sequence[GenTableColumnModel]:
        """根据业务表字段查询业务表字段列表。

        参数:
        - search (dict | None): 查询参数，例如{"table_id": 1}。
        - order_by (list | None): 排序字段列表，每个元素为{"field": "字段名", "order": "asc" | "desc"}。
        - preload (list | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[GenTableColumnModel]: 业务表字段列表信息对象序列。
        """
        return await self.get_list(search=search, order_by=order_by, preload=preload)

    async def create_gen_table_column_crud(self, data: GenTableColumnSchema) -> GenTableColumnModel | None:
        """创建业务表字段。

        参数:
        - data (GenTableColumnSchema): 业务表字段模型。

        返回:
        - GenTableColumnModel | None: 业务表字段列表信息对象。
        """
        return await self.create(data=data)

    async def update_gen_table_column_crud(self, id: int, data: GenTableColumnSchema) -> GenTableColumnModel | None:
        """更新业务表字段。

        参数:
        - id (int): 业务表字段ID。
        - data (GenTableColumnSchema): 业务表字段模型。

        返回:
        - GenTableColumnModel | None: 业务表字段列表信息对象。
        """
        return await self.update(id=id, data=data)

    async def delete_gen_table_column_by_table_id_crud(self, table_ids: list[int]) -> None:
        """根据业务表ID批量删除业务表字段。

        参数:
        - table_ids (list[int]): 业务表ID列表。

        返回:
        - None
        """
        # 先查询出这些表ID对应的所有字段ID
        query = select(GenTableColumnModel.id).where(GenTableColumnModel.table_id.in_(table_ids))
        result = await self.db.execute(query)
        column_ids = [row[0] for row in result.fetchall()]

        # 如果有字段ID，则删除这些字段
        if column_ids:
            await self.delete(ids=column_ids)

    async def delete_gen_table_column_by_column_id_crud(self, column_ids: list[int]) -> None:
        """根据业务表字段ID批量删除业务表字段。

        参数:
        - column_ids (list[int]): 业务表字段ID列表。

        返回:
        - None
        """
        return await self.delete(ids=column_ids)
