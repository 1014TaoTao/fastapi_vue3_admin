import io
import os
import re
import zipfile
from collections.abc import Callable
from typing import Any

import anyio
import sqlglot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlglot.expressions import (
    Alter,
    Comment,
    Create,
    Delete,
    Drop,
    Insert,
    Table,
    TruncateTable,
    Update,
)

from app.common.constant import GenConstant
from app.common.enums import QueueEnum
from app.config.path_conf import BASE_DIR
from app.config.setting import settings
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.modules.system.menu.crud import MenuCRUD
from app.modules.system.menu.schema import MenuCreateSchema
from app.utils.common_util import CamelCaseUtil, compute_menu_route_first_segment, search_to_dict

from .crud import GenTableColumnCRUD, GenTableCRUD
from .gen_util import GenUtils
from .jinja2_template_util import Jinja2TemplateUtil
from .schema import (
    GenSyncColumnChange,
    GenSyncPreviewSchema,
    GenTableColumnOutSchema,
    GenTableColumnSchema,
    GenTableOutSchema,
    GenTableQueryParam,
    GenTableSchema,
)


def handle_service_exception(func: Callable) -> Callable:
    """服务层异步方法装饰器：透传 CustomException，其余异常包装为 CustomException。

    参数:
    - func (Callable): 被装饰的异步可调用对象。

    返回:
    - Callable: 包装后的可调用对象（异步）。
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"{func.__name__}执行失败: {e!s}")

    return wrapper


_MENU_TYPE_CATALOG = 1  # 与 sys_menu.type、前端 MenuTypeEnum.CATALOG 一致
_MENU_TYPE_MENU = 2  # 与 sys_menu.type、前端 MenuTypeEnum.MENU 一致


class GenTableService:
    """代码生成业务表服务层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def _effective_package_name(self, parent_catalog_id: int | None, package_name: str | None) -> str:
        """根据「是否选择上级目录」计算最终包名（分系统根目录）。

        规则（与你描述一致）：
        - **未选上级目录**：认为是「新分系统」，包名固定为 ``module_目录``（即 ``module_xxx``）。
        - **已选上级目录**：认为是「分系统内新模块」，包名继承上级目录对应的 ``module_xxx``。
        """
        pn = (package_name or "").strip()
        # 1) 选择上级目录：从上级菜单 route_path 第一段推断 module_xxx
        if parent_catalog_id is not None:
            m = await MenuCRUD(self.auth, self.db).get(id=parent_catalog_id)
            if not m:
                raise CustomException(msg="上级菜单不存在")
            route_path = (getattr(m, "route_path", None) or "").strip()
            # 期望形如 /module_xxx 或 /module_xxx/yyy
            seg = route_path.strip("/").split("/", 1)[0] if route_path else ""
            seg = (seg or "").strip()
            if seg:
                return seg if seg.startswith("module_") else f"module_{seg}"
            # 路由缺失则回退包名字段
            if pn:
                return pn if pn.startswith("module_") else f"module_{pn}"
            raise CustomException(msg="无法从上级目录推断分系统包名，请先完善上级目录路由")

        # 2) 未选上级目录：以包名字段为准，并确保 module_ 前缀
        if not pn:
            raise CustomException(msg="包名不能为空")
        return pn if pn.startswith("module_") else f"module_{pn}"

    async def _assert_parent_menu_is_catalog(self, parent_menu_id: int | None) -> None:
        """上级菜单仅允许目录：与前端树只展示目录一致，避免挂到菜单/按钮下。"""
        if parent_menu_id is None:
            return

        m = await MenuCRUD(self.auth, self.db).get(id=parent_menu_id)
        if not m:
            raise CustomException(msg="上级菜单不存在")
        if m.type != _MENU_TYPE_CATALOG:
            raise CustomException(msg="上级菜单须选择目录类型")

    @staticmethod
    def _menu_route_first_segment(parent_catalog_id: int | None, package_name: str, module_name: str | None) -> str:
        """前端页面路由首段（与菜单 ``route_path`` 第一段一致）。

        统一规则：始终使用分系统包名 ``module_xxx`` 作为路由首段。
        - **无上级目录**：``/module_xxx/...``（新分系统）
        - **有上级目录**：``/module_xxx/...``（继承上级所属分系统）
        """
        return compute_menu_route_first_segment(parent_catalog_id, package_name, module_name)

    def _catalog_menu_dir_key(self, parent_catalog_id: int | None, package_name: str, module_name: str | None) -> str:
        """菜单上「模块目录」节点的 name（与路由第一段 package 独立）。

        统一为 **目录 → 菜单 → 按钮**：
        - 目录节点固定为 ``module_name``（你填写的“模块”）
        - 是否选择上级目录，仅影响分系统根 ``module_xxx`` 的推断方式（见 ``_effective_package_name``）
        """
        pn = (package_name or "").strip()
        mn = (module_name or "").strip()
        if not pn:
            raise CustomException(msg="包名不能为空")
        if not mn:
            raise CustomException(msg="模块名不能为空")
        return mn

    async def _get_or_create_package_directory_menu(
        self,
        menu_crud: Any,
        parent_catalog_id: int | None,
        package_name: str,
        module_name: str | None,
        business_name: str,
    ) -> int:
        """创建或复用 type=1 模块目录；固定为「目录 → 菜单 → 按钮」中的第一层目录。"""
        pn = (package_name or "").strip()
        if not pn:
            raise CustomException(msg="包名不能为空")
        mn = (module_name or "").strip()
        dir_key = self._catalog_menu_dir_key(parent_catalog_id, pn, module_name)

        if parent_catalog_id is not None:
            existing = await menu_crud.get(name=dir_key, type=_MENU_TYPE_CATALOG, parent_id=parent_catalog_id)
        else:
            existing = await menu_crud.get(name=dir_key, type=_MENU_TYPE_CATALOG, parent_id=(QueueEnum.none.value, None))
        if existing:
            logger.info(f"代码生成：复用模块目录菜单 id={existing.id} name={dir_key!r} parent={parent_catalog_id!r}")
            return int(existing.id)

        route_first = self._menu_route_first_segment(parent_catalog_id, pn, module_name)
        # 目录菜单单段绝对路径（与 sys_menu.json 种子惯例一致，如 /system）；redirect 指向模块根
        catalog_route_path = f"/{route_first}"
        redirect = f"/{route_first}/{mn}"
        # route_name 须唯一且体现「分系统+模块目录」，勿仅用 package（会与 module_example 根混淆）
        catalog_route_name = CamelCaseUtil.snake_to_camel(f"{route_first}_{mn}")
        created = await menu_crud.create(
            MenuCreateSchema(
                name=dir_key,
                type=_MENU_TYPE_CATALOG,
                order=9999,
                permission=None,
                icon="menu",
                route_name=catalog_route_name,
                route_path=catalog_route_path,
                component_path=None,
                redirect=redirect,
                hidden=False,
                keep_alive=True,
                always_show=False,
                title=dir_key,
                params=None,
                affix=False,
                parent_id=parent_catalog_id,
                status=0,
                description="模块目录（代码生成）",
            ),
        )
        logger.info(f"代码生成：新建模块目录菜单 id={created.id} name={dir_key!r} under_parent={parent_catalog_id!r}")
        return int(created.id)

    @staticmethod
    def normalize_and_validate_master_sub(data: GenTableSchema) -> None:
        """主子表业务规则：子表表名与外键列同填或同空；子表表名不得与主表相同。

        参数:
        - data (GenTableSchema): 主表配置。

        返回:
        - None

        异常:
        - CustomException: 规则不满足时抛出。
        """
        sn = data.sub_table_name
        fk = data.sub_table_fk_name
        if bool(sn) ^ bool(fk):
            raise CustomException(msg="子表表名与子表外键列须同时填写或同时留空")
        tn = (data.table_name or "").strip()
        if sn and fk and sn == tn:
            raise CustomException(msg="子表表名不能与主表表名相同")

    @handle_service_exception
    async def get_gen_table_detail(self, table_id: int) -> GenTableOutSchema:
        """获取详细信息。

        参数:
        - auth (AuthSchema): 认证信息。
        - table_id (int): 业务表ID。

        返回:
        - dict: 包含业务表详细信息的字典。
        """
        gen_table = await self.get_gen_table_by_id(table_id)
        return gen_table

    @handle_service_exception
    async def get_gen_table_page(
        self,
        page_no: int,
        page_size: int,
        search: GenTableQueryParam,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[GenTableOutSchema]:
        """分页查询代码生成业务表（数据库 OFFSET/LIMIT）。

        参数:
        - auth (AuthSchema): 认证信息。
        - page_no (int): 页码。
        - page_size (int): 每页条数。
        - search (GenTableQueryParam): 查询条件。
        - order_by (list[dict[str, str]] | None): 排序。

        返回:
        - dict: 分页结果。
        """
        offset = (page_no - 1) * page_size
        order = order_by or [{"created_time": "desc"}]
        return await GenTableCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order,
            search=search_to_dict(search, {}),
            out_schema=GenTableOutSchema,
            preload=["columns"],
        )

    @handle_service_exception
    async def get_gen_db_table_page(
        self,
        page_no: int,
        page_size: int,
        search: GenTableQueryParam,
    ) -> dict[str, Any]:
        """数据库表列表分页（数据库侧 OFFSET/LIMIT）。

        参数:
        - auth (AuthSchema): 认证信息。
        - page_no (int): 页码。
        - page_size (int): 每页条数。
        - search (GenTableQueryParam): 查询条件。

        返回:
        - dict[str, Any]: 含 items、total、has_next 等字段。
        """
        offset = (page_no - 1) * page_size
        items, total = await GenTableCRUD(self.auth, self.db).get_db_table_page(
            table_name=search.table_name,
            table_comment=search.table_comment,
            offset=offset,
            limit=page_size,
        )
        return {
            "items": items,
            "total": total,
            "page_no": page_no,
            "page_size": page_size,
            "has_next": offset + page_size < total,
        }

    @handle_service_exception
    async def get_gen_db_table_list_by_name(self, table_names: list[str]) -> list[GenTableOutSchema]:
        """根据表名称组获取数据库表信息。

        参数:
        - auth (AuthSchema): 认证信息。
        - table_names (list[str]): 业务表名称列表。

        返回:
        - list[GenTableOutSchema]: 包含业务表详细信息的模型列表。
        """
        gen_db_table_list_result = await GenTableCRUD(self.auth, self.db).get_db_table_list_by_names(table_names)

        # 修复：将GenDBTableSchema对象转换为字典后再传递给GenTableOutSchema
        result = [GenTableOutSchema.model_validate(gen_table.model_dump()) for gen_table in gen_db_table_list_result]

        return result

    async def _get_db_table_columns(self, table_name: str) -> list[GenTableColumnOutSchema]:
        """读取物理库表字段并转换为输出模型（供导入/同步/预览使用）。"""
        columns_info = await GenTableColumnCRUD(self.auth, self.db).get_gen_db_table_columns_by_name(table_name)
        return [GenTableColumnOutSchema(**column_info) for column_info in columns_info]

    @handle_service_exception
    async def import_gen_table(self, gen_table_list: list[GenTableOutSchema]) -> bool:
        """导入表结构到生成器。

        参数:
        - auth (AuthSchema): 认证信息。
        - gen_table_list (list[GenTableOutSchema]): 包含业务表详细信息的模型列表。

        返回:
        - bool: 成功时返回True，失败时抛出异常。
        """
        # 检查是否有表需要导入
        if not gen_table_list:
            raise CustomException(msg="导入的表结构不能为空")
        try:
            for table in gen_table_list:
                _row = {k: v for k, v in table.model_dump().items() if k in GenTableSchema.model_fields}
                self.normalize_and_validate_master_sub(GenTableSchema.model_validate(_row))
                table_name = table.table_name
                # 检查表是否已存在
                existing_table = await GenTableCRUD(self.auth, self.db).get_gen_table_by_name(table_name)
                if existing_table:
                    raise CustomException(msg=f"以下表已存在，不能重复导入: {table_name}")
                GenUtils.init_table(table)
                if not table.columns:
                    table.columns = []
                add_gen_table = await GenTableCRUD(self.auth, self.db).add_gen_table(GenTableSchema.model_validate(table.model_dump()))
                gen_table_columns = await self._get_db_table_columns(table_name)
                if len(gen_table_columns) > 0:
                    table.id = add_gen_table.id
                    for column in gen_table_columns:
                        column_schema = GenTableColumnSchema(
                            table_id=table.id,
                            column_name=column.column_name,
                            column_comment=column.column_comment,
                            column_type=column.column_type,
                            column_length=column.column_length,
                            column_default=column.column_default,
                            is_pk=column.is_pk,
                            is_increment=column.is_increment,
                            is_nullable=column.is_nullable,
                            is_unique=column.is_unique,
                            sort=column.sort,
                            python_type=column.python_type,
                            python_field=column.python_field,
                        )
                        GenUtils.init_column_field(column_schema, table)
                        await GenTableColumnCRUD(self.auth, self.db).create_gen_table_column_crud(column_schema)
            return True
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"导入失败, {e!s}")

    @handle_service_exception
    async def create_table(self, sql: str) -> bool | None:
        """创建表结构并导入至代码生成模块。

        参数:
        - auth (AuthSchema): 认证信息。
        - sql (str): 包含`CREATE TABLE`语句的SQL字符串。

        返回:
        - bool | None: 成功时返回True，失败时抛出异常。
        """
        # 验证SQL非空
        if not sql or not sql.strip():
            raise CustomException(msg="SQL语句不能为空")
        try:
            # 解析SQL语句
            sql_statements = sqlglot.parse(sql, dialect=settings.DATABASE_TYPE)
            if not sql_statements:
                raise CustomException(msg="无法解析SQL语句，请检查SQL语法")

            # 校验 SQL 是否为合法的建表语句集合：
            # - 允许：CREATE TABLE + COMMENT ON TABLE/COLUMN +（可选）ALTER TABLE ADD CONSTRAINT ... FOREIGN KEY ...
            # - 禁止：DROP/DELETE/INSERT/UPDATE/TRUNCATE 等破坏性语句
            has_create = any(isinstance(s, Create) for s in sql_statements)
            if not has_create:
                raise CustomException(msg="sql语句不是合法的建表语句：缺少 CREATE TABLE")

            forbidden = (Delete, Drop, Insert, TruncateTable, Update)
            if any(isinstance(s, forbidden) for s in sql_statements):
                raise CustomException(msg="sql语句包含禁止的关键操作（DROP/DELETE/INSERT/UPDATE/TRUNCATE）")

            # 获取要创建的表名
            table_names = []
            for sql_statement in sql_statements:
                if isinstance(sql_statement, Create):
                    table = sql_statement.find(Table)
                    if table and table.name:
                        table_names.append(table.name)
            table_names = list(set(table_names))

            # 创建CRUD实例
            gen_table_crud = GenTableCRUD(self.auth, self.db)

            # 检查每个表是否已存在
            for table_name in table_names:
                # 检查数据库中是否已存在该表
                if await gen_table_crud.check_table_exists(table_name):
                    raise CustomException(msg=f"表 {table_name} 已存在，请检查并修改表名后重试")

                # 检查代码生成模块中是否已导入该表
                existing_table = await gen_table_crud.get_gen_table_by_name(table_name)
                if existing_table:
                    raise CustomException(msg=f"表 {table_name} 已在代码生成模块中存在，请检查并修改表名后重试")

            # 表不存在，执行SQL语句创建表
            for sql_statement in sql_statements:
                # 只执行白名单语句：Create / Comment /（受限）Alter
                if not isinstance(sql_statement, (Create, Comment, Alter)):
                    continue
                exc_sql = sql_statement.sql(dialect=settings.DATABASE_TYPE)
                logger.info(f"执行SQL语句: {exc_sql}")

                # ALTER 仅允许添加外键约束，避免任意 ALTER 带来的破坏性
                if isinstance(sql_statement, Alter):
                    upper = exc_sql.upper()
                    allow = "ALTER TABLE" in upper and "ADD" in upper and "CONSTRAINT" in upper and "FOREIGN KEY" in upper and "DROP" not in upper and "RENAME" not in upper and "SET " not in upper
                    if not allow:
                        raise CustomException(msg="仅允许 ALTER TABLE ADD CONSTRAINT ... FOREIGN KEY ...（拒绝其它 ALTER）")
                if not await gen_table_crud.execute_sql(exc_sql):
                    raise CustomException(msg=f"执行SQL语句 {exc_sql} 失败，请检查数据库")

            # 建表成功后自动导入到代码生成模块
            if table_names:
                gen_table_list = await self.get_gen_db_table_list_by_name(table_names)
                if gen_table_list:
                    await self.import_gen_table(gen_table_list)

            return True

        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"创建表结构失败: {e!s}")

    @handle_service_exception
    async def update_gen_table(self, data: GenTableSchema, table_id: int) -> GenTableOutSchema:
        """编辑业务表信息。

        参数:
        - auth (AuthSchema): 认证信息。
        - data (GenTableSchema): 包含业务表详细信息的模型。
        - table_id (int): 业务表ID。

        返回:
        - dict[str, Any]: 更新后的业务表信息。
        """
        # 处理params为None的情况
        gen_table_info = await self.get_gen_table_by_id(table_id)
        if gen_table_info.id:
            try:
                self.normalize_and_validate_master_sub(data)
                await self._assert_parent_menu_is_catalog(data.parent_menu_id)
                # 直接调用edit_gen_table方法，它会在内部处理排除嵌套字段的逻辑
                result = await GenTableCRUD(self.auth, self.db).edit_gen_table(table_id, data)
                if not result:
                    raise CustomException(msg="更新业务表信息失败")

                if data.columns is not None:
                    db_columns = await GenTableColumnCRUD(self.auth, self.db).list_gen_table_column_crud(search={"table_id": table_id})
                    db_column_map = {c.column_name: c for c in db_columns if c.column_name}
                    submitted_names = {c.column_name for c in data.columns if hasattr(c, "column_name") and c.column_name}

                    for gen_table_column in data.columns:
                        col_id = getattr(gen_table_column, "id", None)
                        col_name = getattr(gen_table_column, "column_name", None)
                        if col_id and col_name and col_name in db_column_map:
                            # 只更新前端实际修改的字段（利用 Pydantic model_fields_set）
                            update_data = gen_table_column.model_dump(exclude_unset=True, exclude={"id", "super_column"})
                            if update_data:
                                await GenTableColumnCRUD(self.auth, self.db).update(id=col_id, data=GenTableColumnSchema(**update_data))
                        else:
                            # 新增列：前端新增但库中无对应记录
                            column_schema = GenTableColumnSchema(
                                table_id=table_id,
                                **gen_table_column.model_dump(exclude={"id", "super_column"}),
                            )
                            GenUtils.init_column_field(column_schema, gen_table_info)
                            await GenTableColumnCRUD(self.auth, self.db).create_gen_table_column_crud(column_schema)

                    # 删除前端已移除的列
                    for db_name, db_col in db_column_map.items():
                        if db_name not in submitted_names:
                            db_id = getattr(db_col, "id", None)
                            if db_id:
                                await GenTableColumnCRUD(self.auth, self.db).delete(ids=[db_id])
                # 重新获取带有预加载关系的对象，避免懒加载导致的MissingGreenlet错误
                updated_gen_table = await GenTableCRUD(self.auth, self.db).get_gen_table_by_id(table_id, preload=["columns"])
                out = GenTableOutSchema.model_validate(updated_gen_table)
                await self.set_pk_column(out)
                await self.hydrate_sub_table(out)
                return out
            except CustomException:
                raise
            except Exception as e:
                raise CustomException(msg=str(e))
        else:
            raise CustomException(msg="业务表不存在")

    @handle_service_exception
    async def delete_gen_table(self, ids: list[int]) -> None:
        """删除业务表信息（先删字段，再删表）。

        参数:
        - auth (AuthSchema): 认证信息。
        - ids (list[int]): 业务表ID列表。

        返回:
        - None
        """
        # 验证ID列表非空
        if not ids:
            raise CustomException(msg="ID列表不能为空")

        try:
            # 先删除相关的字段信息
            await GenTableColumnCRUD(self.auth, self.db).delete_gen_table_column_by_table_id_crud(ids)
            # 再删除表信息
            await GenTableCRUD(self.auth, self.db).delete_gen_table(ids)
        except Exception as e:
            raise CustomException(msg=str(e))

    @handle_service_exception
    async def get_gen_table_by_id(self, table_id: int) -> GenTableOutSchema:
        """获取需要生成代码的业务表详细信息。

        参数:
        - auth (AuthSchema): 认证信息。
        - table_id (int): 业务表ID。

        返回:
        - GenTableOutSchema: 业务表详细信息模型。
        """
        gen_table = await GenTableCRUD(self.auth, self.db).get_gen_table_by_id(table_id, preload=["columns"])
        if not gen_table:
            raise CustomException(msg="业务表不存在")

        result = GenTableOutSchema.model_validate(gen_table)
        await self.set_pk_column(result)
        await self.hydrate_sub_table(result)
        return result

    @handle_service_exception
    async def preview_code(self, table_id: int) -> dict[str, Any]:
        """预览代码（根据模板渲染内存结果）。

        参数:
        - auth (AuthSchema): 认证信息。
        - table_id (int): 业务表ID。

        返回:
        - dict[str, Any]: 文件名到渲染内容的映射。
        """
        raw = await GenTableCRUD(self.auth, self.db).get_gen_table_by_id(table_id, preload=["columns"])
        if not raw:
            raise CustomException(msg="业务表不存在")
        gen_table = GenTableOutSchema.model_validate(raw)
        await self.set_pk_column(gen_table)
        await self.hydrate_sub_table(gen_table)
        self._assert_master_sub_config_valid(gen_table)
        # 预览回显的路径/包名规则必须与「写入本地」一致：
        # - 选择上级目录：继承上级目录所属 module_xxx
        # - 未选上级目录：使用表单包名（并补齐 module_ 前缀）
        gen_table.package_name = await self._effective_package_name(gen_table.parent_menu_id, gen_table.package_name)
        # 子表与主表同分系统/同模块
        if gen_table.sub and gen_table.sub_table:
            gen_table.sub_table.package_name = gen_table.package_name
            if not (gen_table.sub_table.module_name or "").strip():
                gen_table.sub_table.module_name = gen_table.module_name
        env = Jinja2TemplateUtil.get_env()
        context = Jinja2TemplateUtil.prepare_context(gen_table)
        template_list = Jinja2TemplateUtil.get_template_list()
        preview_code_result: dict[str, Any] = {}
        for template in template_list:
            try:
                render_content = await env.get_template(template).render_async(**context)
                out_key = Jinja2TemplateUtil.get_file_name(template, gen_table)
                preview_code_result[out_key] = render_content
            except Exception as e:
                logger.error(f"渲染模板 {template} 时出错: {e!s}")
                out_key = Jinja2TemplateUtil.get_file_name(template, gen_table)
                preview_code_result[out_key] = f"渲染错误: {e!s}"
        if gen_table.sub and gen_table.sub_table:
            sub_ctx = Jinja2TemplateUtil.prepare_sub_render_context(gen_table, gen_table.sub_table)
            sub_table = gen_table.sub_table
            sub_template_list = Jinja2TemplateUtil.get_sub_table_template_list()
            for template in sub_template_list:
                try:
                    render_content = await env.get_template(template).render_async(**sub_ctx)
                    out_key = Jinja2TemplateUtil.get_file_name(template, sub_table)
                    preview_code_result[out_key] = render_content
                except Exception as e:
                    logger.error(f"渲染子表模板 {template} 时出错: {e!s}")
                    out_key = Jinja2TemplateUtil.get_file_name(template, sub_table)
                    preview_code_result[out_key] = f"渲染错误: {e!s}"
        return preview_code_result

    @handle_service_exception
    async def generate_code(self, table_name: str) -> bool:
        """生成代码至指定路径（安全写入+可跳过覆盖）。

        菜单固定为 **目录(type=1) + 菜单(type=2) + 按钮(type=3)**：
        - **目录层(name)**：固定为你填写的 ``module_name``（模块）
        - **分系统根(package_name)**：
          - 选上级目录：继承上级目录所属 ``module_xxx``
          - 未选上级目录：使用你填写的包名（自动补齐 ``module_`` 前缀）
        - **页面路由**：``/{module_xxx}/{module_name}/{business_path}``
        - **组件路径**：``module_xxx/module_name/business_path/index``
        - **后端 HTTP 接口前缀**：由动态路由发现容器提供 ``/xxx``（``module_xxx``→去掉 ``module_``）

        参数:
        - auth (AuthSchema): 认证信息。
        - table_name (str): 业务表名。

        返回:
        - bool: 生成是否成功。
        """
        # 验证表名非空
        if not table_name or not table_name.strip():
            raise CustomException(msg="表名不能为空")
        env = Jinja2TemplateUtil.get_env()
        render_info = await self.__get_gen_render_info(table_name)
        gen_table_schema: GenTableOutSchema = render_info[3]

        # 按“上级目录”规则矫正最终包名（分系统根）
        gen_table_schema.package_name = await self._effective_package_name(gen_table_schema.parent_menu_id, gen_table_schema.package_name)
        # 统一权限前缀（对齐 module_example/demo）：
        # - module_xxx:module_name（操作在按钮/模板中追加 :query/:create...）
        pn = (gen_table_schema.package_name or "").strip()
        mn = (gen_table_schema.module_name or "").strip()
        if not mn:
            raise CustomException(msg="模块名不能为空")
        permission_prefix = ":".join([s for s in [pn, mn] if s])
        if not gen_table_schema.function_name:
            raise CustomException(msg="功能名称不能为空")
        if not gen_table_schema.package_name:
            raise CustomException(msg="包名不能为空")

        # 1. 先写代码文件（风险最高，放最前，失败不产生菜单孤儿数据）
        async def _write_templates(templates: list[str], ctx: dict[str, Any], table_schema: GenTableOutSchema) -> None:
            for template in templates:
                try:
                    render_content = await env.get_template(template).render_async(**ctx)
                    file_name = Jinja2TemplateUtil.get_file_name(template, table_schema)
                    full_path = BASE_DIR.parent.joinpath(file_name)
                    gen_path = str(full_path)
                    os.makedirs(os.path.dirname(gen_path), exist_ok=True)
                    await anyio.Path(gen_path).write_text(render_content, encoding="utf-8")
                    # Python 插件目录需保证包层级可导入：为分系统/模块目录补齐 __init__.py
                    pn_inner = (table_schema.package_name or "").strip()
                    mn_inner = (table_schema.module_name or "").strip()
                    if pn_inner and mn_inner:
                        plugin_base = BASE_DIR.parent.joinpath(f"backend/app/plugin/{pn_inner}")
                        module_base = plugin_base.joinpath(mn_inner)
                        for d in (plugin_base, module_base):
                            init_path = d.joinpath("__init__.py")
                            if not init_path.exists():
                                os.makedirs(str(d), exist_ok=True)
                                await anyio.Path(str(init_path)).write_text("# -*- coding: utf-8 -*-", encoding="utf-8")
                except Exception as e:
                    raise CustomException(msg=f"渲染模板失败，表名：{table_schema.table_name}，详细错误信息：{e!s}")

        await _write_templates(render_info[0], render_info[2], gen_table_schema)
        if gen_table_schema.sub and gen_table_schema.sub_table:
            gen_table_schema.sub_table.package_name = gen_table_schema.package_name
            if not (gen_table_schema.sub_table.module_name or "").strip():
                gen_table_schema.sub_table.module_name = gen_table_schema.module_name
            sub_ctx = Jinja2TemplateUtil.prepare_sub_render_context(gen_table_schema, gen_table_schema.sub_table)
            sub_templates = Jinja2TemplateUtil.get_sub_table_template_list()
            await _write_templates(sub_templates, sub_ctx, gen_table_schema.sub_table)

        # 2. 代码成功写入后，再创建菜单（避免失败时产生孤儿菜单数据）
        menu_crud = MenuCRUD(self.auth, self.db)
        await self._assert_parent_menu_is_catalog(gen_table_schema.parent_menu_id)
        # 1. 目录 + 菜单 + 按钮：先取/建模块目录（名称规则见 _catalog_menu_dir_key）
        dir_menu_id = await self._get_or_create_package_directory_menu(
            menu_crud,
            gen_table_schema.parent_menu_id,
            gen_table_schema.package_name,
            gen_table_schema.module_name,
            gen_table_schema.business_name or "",
        )

        # 检查同一模块目录下是否已有同名功能菜单（避免与其它模块下的同名功能冲突）
        existing_func_menu = await menu_crud.get(
            name=gen_table_schema.function_name,
            type=_MENU_TYPE_MENU,
            parent_id=dir_menu_id,
        )
        if existing_func_menu:
            raise CustomException(msg=f"该模块目录下功能菜单「{gen_table_schema.function_name}」已存在，不能重复创建")
        route_seg = self._menu_route_first_segment(
            gen_table_schema.parent_menu_id,
            gen_table_schema.package_name or "",
            gen_table_schema.module_name,
        )
        _pn = (gen_table_schema.package_name or "").strip()
        _mn = (gen_table_schema.module_name or "").strip()
        if not _mn:
            raise CustomException(msg="模块名不能为空")

        # 与 Jinja2TemplateUtil.get_file_name 统一：module_xxx/{module_name}
        _route_path = f"/{route_seg}/{_mn}"
        _component_path = f"{_pn}/{_mn}/index"
        # 创建功能菜单（类型=2：菜单）
        parent_menu = await menu_crud.create(
            MenuCreateSchema(
                name=gen_table_schema.function_name,
                type=_MENU_TYPE_MENU,
                order=9999,
                permission=f"{permission_prefix}:query",
                icon="menu",
                route_name=CamelCaseUtil.snake_to_camel(_mn),
                route_path=_route_path,
                component_path=_component_path,
                redirect=None,
                hidden=False,
                keep_alive=True,
                always_show=False,
                title=gen_table_schema.function_name,
                params=None,
                affix=False,
                parent_id=dir_menu_id,  # 使用目录菜单ID或用户指定的parent_menu_id作为父ID
                status=0,
                description=f"{gen_table_schema.function_name}功能菜单",
            ),
        )
        # 创建按钮权限（类型=3：按钮/权限）
        buttons = [
            {
                "name": f"{gen_table_schema.function_name}查询",
                "permission": f"{permission_prefix}:query",
                "order": 1,
            },
            {
                "name": f"{gen_table_schema.function_name}详情",
                "permission": f"{permission_prefix}:detail",
                "order": 2,
            },
            {
                "name": f"{gen_table_schema.function_name}新增",
                "permission": f"{permission_prefix}:create",
                "order": 3,
            },
            {
                "name": f"{gen_table_schema.function_name}修改",
                "permission": f"{permission_prefix}:update",
                "order": 4,
            },
            {
                "name": f"{gen_table_schema.function_name}删除",
                "permission": f"{permission_prefix}:delete",
                "order": 5,
            },
            {
                "name": f"{gen_table_schema.function_name}批量状态修改",
                "permission": f"{permission_prefix}:patch",
                "order": 6,
            },
            {
                "name": f"{gen_table_schema.function_name}导出",
                "permission": f"{permission_prefix}:export",
                "order": 7,
            },
            {
                "name": f"{gen_table_schema.function_name}导入",
                "permission": f"{permission_prefix}:import",
                "order": 8,
            },
            {
                "name": f"{gen_table_schema.function_name}下载导入模板",
                "permission": f"{permission_prefix}:download",
                "order": 9,
            },
        ]
        for button in buttons:
            existing_btn = await menu_crud.get(
                permission=button["permission"],
                type=3,
                parent_id=parent_menu.id,
            )
            if existing_btn:
                logger.info(f"按钮权限已存在，跳过创建: {button['permission']}")
                continue
            await menu_crud.create(
                MenuCreateSchema(
                    name=button["name"],
                    type=3,
                    order=button["order"],
                    permission=button["permission"],
                    icon=None,
                    route_name=None,
                    route_path=None,
                    component_path=None,
                    redirect=None,
                    hidden=False,
                    keep_alive=True,
                    always_show=False,
                    title=button["name"],
                    params=None,
                    affix=False,
                    parent_id=parent_menu.id,
                    status=0,
                    description=f"{gen_table_schema.function_name}功能按钮",
                ),
            )
            logger.info(f"成功创建按钮权限: {button['name']}")
        logger.info(f"成功创建{gen_table_schema.function_name}菜单及按钮权限")

        return True

    @handle_service_exception
    async def batch_gen_code(self, table_names: list[str]) -> tuple[bytes, list[str]]:
        """批量生成代码并打包为ZIP。
        - 备注：内存生成并压缩，兼容多模板类型；供下载使用。

        参数:
        - auth (AuthSchema): 认证信息。
        - table_names (list[str]): 业务表名列表。

        返回:
        - bytes: 包含所有生成代码的ZIP文件内容。
        """
        valid_names = [t.strip() for t in table_names if t and str(t).strip()]
        if not valid_names:
            raise CustomException(msg="表名列表不能为空")
        zip_buffer = io.BytesIO()
        file_count = 0
        failed_tables: list[str] = []
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for table_name in valid_names:
                try:
                    env = Jinja2TemplateUtil.get_env()
                    render_info = await self.__get_gen_render_info(table_name)
                    gen_tbl = render_info[3]
                    for template_file, output_file in zip(render_info[0], render_info[1], strict=False):
                        render_content = await env.get_template(template_file).render_async(**render_info[2])
                        zip_file.writestr(output_file, render_content)
                        file_count += 1
                    if gen_tbl.sub and gen_tbl.sub_table:
                        sub_ctx = Jinja2TemplateUtil.prepare_sub_render_context(gen_tbl, gen_tbl.sub_table)
                        sub_tbl = gen_tbl.sub_table
                        sub_template_list = Jinja2TemplateUtil.get_sub_table_template_list()
                        for template_file in sub_template_list:
                            render_content = await env.get_template(template_file).render_async(**sub_ctx)
                            out_path = Jinja2TemplateUtil.get_file_name(template_file, sub_tbl)
                            zip_file.writestr(out_path, render_content)
                            file_count += 1
                except Exception as e:
                    logger.error(f"批量生成代码时处理表 {table_name} 出错: {e!s}")
                    failed_tables.append(table_name)
                    # 继续处理其他表，不中断整个过程
                    continue
        zip_data = zip_buffer.getvalue()
        zip_buffer.close()
        if file_count == 0:
            raise CustomException(msg="未能生成任何代码文件：请检查所选表是否存在于代码生成配置中，或主子表、字段配置是否正确")
        return zip_data, failed_tables

    @handle_service_exception
    async def sync_db(self, table_name: str, _sync_sub: bool = True) -> None:
        """同步数据库表结构到业务表。

        参数:
        - auth (AuthSchema): 认证信息。
        - table_name (str): 业务表名。

        返回:
        - None
        """
        # 验证表名非空
        if not table_name or not table_name.strip():
            raise CustomException(msg="表名不能为空")
        gen_table = await GenTableCRUD(self.auth, self.db).get_gen_table_by_name(table_name, preload=["columns"])
        if not gen_table:
            raise CustomException(msg="业务表不存在")
        table = GenTableOutSchema.model_validate(gen_table)
        if not table.id:
            raise CustomException(msg="业务表ID不能为空")
        table_columns = table.columns or []
        table_column_map = {column.column_name: column for column in table_columns}
        # 确保db_table_columns始终是列表类型，避免None值
        db_table_columns = await self._get_db_table_columns(table_name)
        db_table_columns = [col for col in db_table_columns if col is not None]
        db_table_column_names = [column.column_name for column in db_table_columns]
        try:
            preserve_keys = {
                "dict_type",
                "query_type",
                "python_field",
                "python_type",
                "is_insert",
                "is_edit",
                "is_list",
                "is_query",
                "sort",
            }

            for column in db_table_columns:
                GenUtils.init_column_field(column, table)
                if column.column_name in table_column_map:
                    prev_column = table_column_map[column.column_name]
                    if getattr(prev_column, "id", None):
                        column.id = prev_column.id
                    prev_dump = prev_column.model_dump() if hasattr(prev_column, "model_dump") else {}
                    for k in preserve_keys:
                        if k in prev_dump and prev_dump.get(k) not in (None, ""):
                            setattr(column, k, prev_dump.get(k))
                    # html_type：保留用户显式选择的非 input；若仍是默认 input，则允许按 DB 重新推断
                    prev_html = prev_dump.get("html_type")
                    if prev_html not in (None, "", GenConstant.HTML_INPUT):
                        column.html_type = prev_html
                    # 主键强约束：避免历史配置导致主键出现在新增/编辑/列表/查询
                    if bool(getattr(column, "is_pk", False)):
                        column.is_insert = False
                        column.is_edit = False
                        column.is_list = False
                        column.is_query = False
                        column.query_type = None
                    # is_nullable：主键列以 DB 为准，其余保留用户设置
                    if not bool(getattr(column, "is_pk", False)) and hasattr(prev_column, "is_nullable"):
                        column.is_nullable = prev_column.is_nullable

                    # 转换为 GenTableColumnSchema，排除 super_column 等输出专用字段
                    column_data = GenTableColumnSchema(**column.model_dump(exclude={"super_column"}))
                    if hasattr(column, "id") and column.id:
                        await GenTableColumnCRUD(self.auth, self.db).update_gen_table_column_crud(column.id, column_data)
                    else:
                        await GenTableColumnCRUD(self.auth, self.db).create_gen_table_column_crud(column_data)
                else:
                    # 设置table_id以确保新字段能正确关联到表
                    column.table_id = table.id
                    # 转换为 GenTableColumnSchema，排除 super_column 等输出专用字段
                    column_data = GenTableColumnSchema(**column.model_dump(exclude={"super_column"}))
                    await GenTableColumnCRUD(self.auth, self.db).create_gen_table_column_crud(column_data)
            del_columns = [column for column in table_columns if column.column_name not in db_table_column_names]
            if del_columns:
                for column in del_columns:
                    if hasattr(column, "id") and column.id:
                        await GenTableColumnCRUD(self.auth, self.db).delete_gen_table_column_by_column_id_crud([column.id])

            # 主子表：若子表也已导入生成器，则一并同步子表配置
            sn = (table.sub_table_name or "").strip()
            fk = (table.sub_table_fk_name or "").strip()
            if _sync_sub and sn and fk:
                sub_cfg = await GenTableCRUD(self.auth, self.db).get_gen_table_by_name(sn)
                if sub_cfg:
                    await self.sync_db(sn, _sync_sub=False)
        except Exception as e:
            raise CustomException(msg=f"同步失败: {e!s}")

    async def hydrate_sub_table(self, gen_table: GenTableOutSchema) -> None:
        """主子表：优先使用已导入的子表配置，否则回退为只读 DB 结构。

        对齐 RuoYi：子表宜为独立 gen_table；主表仅引用。

        参数:
        - auth (AuthSchema): 认证信息。
        - gen_table (GenTableOutSchema): 主表输出模型（原地填充 sub_table、master_sub_hint 等）。

        返回:
        - None
        """
        gen_table.master_sub_hint = None
        sub_name_raw = (gen_table.sub_table_name or "").strip()
        fk_raw = (gen_table.sub_table_fk_name or "").strip()
        if not sub_name_raw and not fk_raw:
            gen_table.sub = False
            gen_table.sub_table = None
            return
        if sub_name_raw and not fk_raw:
            gen_table.sub = False
            gen_table.sub_table = None
            gen_table.master_sub_hint = "已填写子表表名，请同时填写「子表外键列」后再保存"
            return
        if fk_raw and not sub_name_raw:
            gen_table.sub = False
            gen_table.sub_table = None
            gen_table.master_sub_hint = "已填写子表外键列，请同时填写「子表表名」后再保存"
            return
        if sub_name_raw == (gen_table.table_name or "").strip():
            gen_table.sub = False
            gen_table.sub_table = None
            gen_table.master_sub_hint = "子表表名不能与主表表名相同"
            return

        # 1) 若子表已作为 gen_table 导入，则使用其 columns 配置（可控、可复用）
        try:
            sub_cfg_model = await GenTableCRUD(self.auth, self.db).get_gen_table_by_name(sub_name_raw, preload=["columns"])
        except Exception:
            sub_cfg_model = None
        if sub_cfg_model:
            sub_cfg = GenTableOutSchema.model_validate(sub_cfg_model)
            await self.set_pk_column(sub_cfg)
            # 校验外键列存在于子表配置中
            fk_names = {c.column_name for c in (sub_cfg.columns or []) if c.column_name}
            if fk_raw not in fk_names:
                gen_table.sub = False
                gen_table.sub_table = None
                gen_table.master_sub_hint = f"子表「{sub_name_raw}」已导入生成器，但其字段配置中不存在外键列「{fk_raw}」。请先在子表的字段配置中同步/保存后再生成。"
                return
            gen_table.sub = True
            gen_table.sub_table = sub_cfg
            gen_table.master_sub_hint = "主子表已启用：子表字段来自「已导入的子表配置」（更可控、可复用）。如需调整子表字段，请在列表中打开该子表进行配置。"
            return

        # 2) 回退：仅从 DB 读取结构（只读，无法配置子表字段）
        try:
            gen_table_columns = await self._get_db_table_columns(sub_name_raw)
        except Exception as e:
            # 读取失败时给出明确提示（不再重复调用同一方法——必然再次失败）
            gen_table.sub = False
            gen_table.sub_table = None
            gen_table.master_sub_hint = f"无法读取子表结构：{e!s}"
            return
        if not gen_table_columns:
            gen_table.sub = False
            gen_table.sub_table = None
            gen_table.master_sub_hint = f"当前数据库中不存在表「{sub_name_raw}」或该表无列，请先建表再配置主子表"
            return
        fk_names = {c.column_name for c in gen_table_columns if c.column_name}
        if fk_raw not in fk_names:
            gen_table.sub = False
            gen_table.sub_table = None
            gen_table.master_sub_hint = f"子表「{sub_name_raw}」中不存在名为「{fk_raw}」的列，请核对外键列名"
            return
        table_comment = await GenTableCRUD(self.auth, self.db).get_db_table_comment(sub_name_raw)
        sub = GenTableOutSchema.model_validate(
            {
                "id": -1,
                "table_name": sub_name_raw,
                "table_comment": table_comment or None,
                "class_name": GenUtils.convert_class_name(sub_name_raw),
                "package_name": gen_table.package_name,
                "module_name": sub_name_raw,
                "business_name": sub_name_raw,
                "function_name": re.sub(r"(?:表|测试)", "", table_comment or "") or sub_name_raw,
                "sub_table_name": None,
                "sub_table_fk_name": None,
                "parent_menu_id": gen_table.parent_menu_id,
                "columns": [],
                "sub": False,
                "sub_table": None,
            },
        )
        for column in gen_table_columns:
            col_dump = column.model_dump()
            col_dump["table_id"] = -1
            col_schema = GenTableColumnSchema.model_validate(col_dump)
            GenUtils.init_column_field(col_schema, sub)
            if sub.columns is None:
                sub.columns = []
            sub.columns.append(GenTableColumnOutSchema(**col_schema.model_dump()))
        await self.set_pk_column(sub)
        gen_table.sub = True
        gen_table.sub_table = sub
        gen_table.master_sub_hint = f"主子表已启用：当前子表仅从数据库结构读取（只读）。若想可配置子表字段，请先在「导入」中把子表「{sub_name_raw}」也导入生成器。"

    def _sync_preview_diff(
        self,
        current_cols: list[GenTableColumnOutSchema],
        db_cols: list[GenTableColumnOutSchema],
    ) -> tuple[list[str], list[str], list[GenSyncColumnChange], int]:
        cur_map = {c.column_name: c for c in (current_cols or []) if c and c.column_name}
        db_map = {c.column_name: c for c in (db_cols or []) if c and c.column_name}

        cur_names = set(cur_map.keys())
        db_names = set(db_map.keys())
        added = sorted(db_names - cur_names)
        removed = sorted(cur_names - db_names)

        changed: list[GenSyncColumnChange] = []
        unchanged = 0

        keys = [
            "column_type",
            "column_comment",
            "column_default",
            "column_length",
            "is_pk",
            "is_increment",
            "is_nullable",
            "is_unique",
        ]
        for name in sorted(cur_names & db_names):
            before = cur_map[name]
            after = db_map[name]
            diff_fields: list[str] = []
            b_dump = before.model_dump()
            a_dump = after.model_dump()
            for k in keys:
                if b_dump.get(k) != a_dump.get(k):
                    diff_fields.append(k)
            if diff_fields:
                changed.append(
                    GenSyncColumnChange(
                        column_name=name,
                        change_fields=diff_fields,
                        before={k: b_dump.get(k) for k in keys},
                        after={k: a_dump.get(k) for k in keys},
                    ),
                )
            else:
                unchanged += 1

        return added, removed, changed, unchanged

    @handle_service_exception
    async def sync_db_preview(self, table_name: str) -> GenSyncPreviewSchema:
        """同步数据库前差异预览（主表 + 可选子表）。

        参数:
        - auth (AuthSchema): 认证信息。
        - table_name (str): 主表物理表名。

        返回:
        - dict[str, Any]: 预览差异结构（可序列化）。

        异常:
        - CustomException: 表名无效或业务表不存在等。
        """
        if not table_name or not table_name.strip():
            raise CustomException(msg="表名不能为空")
        gen_table = await GenTableCRUD(self.auth, self.db).get_gen_table_by_name(table_name, preload=["columns"])
        if not gen_table:
            raise CustomException(msg="业务表不存在")

        table = GenTableOutSchema.model_validate(gen_table)
        if not table.id:
            raise CustomException(msg="业务表ID不能为空")

        db_cols = await self._get_db_table_columns(table_name)
        added, removed, changed, unchanged = self._sync_preview_diff(
            current_cols=table.columns or [],
            db_cols=db_cols or [],
        )
        preview = GenSyncPreviewSchema(
            table_name=table_name,
            added=added,
            removed=removed,
            changed=changed,
            unchanged=unchanged,
        )

        # 子表差异：如果启用主子表，则同时预览子表（无论子表是否已导入）
        sn = (table.sub_table_name or "").strip()
        fk = (table.sub_table_fk_name or "").strip()
        if sn and fk:
            preview.sub_table_name = sn
            # 优先取“已导入的子表配置”，否则用 DB 结构（只读）
            sub_cfg = await GenTableCRUD(self.auth, self.db).get_gen_table_by_name(sn, preload=["columns"])
            if sub_cfg:
                cur_sub_cols = GenTableOutSchema.model_validate(sub_cfg).columns or []
            else:
                cur_sub_cols = []
            db_sub_cols = await self._get_db_table_columns(sn)
            s_added, s_removed, s_changed, s_unchanged = self._sync_preview_diff(
                current_cols=cur_sub_cols,
                db_cols=db_sub_cols or [],
            )
            preview.sub = GenSyncPreviewSchema(
                table_name=sn,
                added=s_added,
                removed=s_removed,
                changed=s_changed,
                unchanged=s_unchanged,
            )

        return preview

    @staticmethod
    def _assert_master_sub_config_valid(gen_table: GenTableOutSchema) -> None:
        """预览/生成前校验主子表配置是否可用。"""
        sn = (gen_table.sub_table_name or "").strip()
        fk = (gen_table.sub_table_fk_name or "").strip()
        if not sn and not fk:
            return
        if not sn or not fk:
            raise CustomException(msg=gen_table.master_sub_hint or "子表表名与子表外键列须同时填写或同时留空")
        if not gen_table.sub_table:
            raise CustomException(msg=gen_table.master_sub_hint or "无法生成主子表代码：请确认子表已在当前数据库中存在，且外键列名正确")

    async def set_pk_column(self, gen_table: GenTableOutSchema) -> None:
        """设置主键列信息（主表/子表）。
        - 备注：同时兼容`pk`布尔与`is_pk == '1'`字符串两种标识。

        参数:
        - gen_table (GenTableOutSchema): 业务表详细信息模型。

        返回:
        - None
        """
        if gen_table.columns:
            for column in gen_table.columns:
                is_pk = getattr(column, "is_pk", False)
                if bool(is_pk) if isinstance(is_pk, bool) else str(is_pk) == "1":
                    gen_table.pk_column = column
                    break
        # 如果没有找到主键列且有列存在，使用第一个列作为主键
        if gen_table.pk_column is None and gen_table.columns:
            gen_table.pk_column = gen_table.columns[0]

    async def __get_gen_render_info(self, table_name: str) -> list[Any]:
        """获取生成代码渲染模板相关信息。

        参数:
        - auth (AuthSchema): 认证对象。
        - table_name (str): 业务表名称。

        返回:
        - list[Any]: [模板列表, 输出文件名列表, 渲染上下文, 业务表对象]。

        异常:
        - CustomException: 当业务表不存在或数据转换失败时抛出。
        """
        gen_table_model = await GenTableCRUD(self.auth, self.db).get_gen_table_by_name(table_name, preload=["columns"])
        # 检查表是否存在
        if gen_table_model is None:
            raise CustomException(msg=f"业务表 {table_name} 不存在")
        gen_table = GenTableOutSchema.model_validate(gen_table_model)
        # 生成代码时按“上级目录”规则矫正最终包名（不落库，仅影响本次生成/预览/下载/写入）
        gen_table.package_name = await self._effective_package_name(gen_table.parent_menu_id, gen_table.package_name)
        await self.set_pk_column(gen_table)
        await self.hydrate_sub_table(gen_table)
        self._assert_master_sub_config_valid(gen_table)
        context = Jinja2TemplateUtil.prepare_context(gen_table)
        template_list = Jinja2TemplateUtil.get_template_list()
        output_files = [Jinja2TemplateUtil.get_file_name(template, gen_table) for template in template_list]
        return [template_list, output_files, context, gen_table]
