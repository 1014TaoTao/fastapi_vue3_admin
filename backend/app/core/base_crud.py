from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar, cast

from pydantic import BaseModel
from sqlalchemy import asc, delete, desc, false, func, select, true, update
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.core.base_model import ModelMixin
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException

OutSchemaType = TypeVar("OutSchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# 操作符 → 方法名映射，留给 _resolve_condition 运行时根据具体 attr 调用
# 因为不同列的 ColumnElement 类型不同，不能提取为类级常量
_OPERATOR_MAP: dict[str, str] = {
    "!=": "__ne__", "ne": "__ne__",
    ">": "__gt__", "gt": "__gt__",
    ">=": "__ge__", "ge": "__ge__",
    "<": "__lt__", "lt": "__lt__",
    "<=": "__le__", "le": "__le__",
    "eq": "__eq__", "==": "__eq__",
}


class CRUDBase[ModelType: ModelMixin, CreateSchemaType, UpdateSchemaType]:
    """事务边界在 HTTP 层（db_getter 有 session.begin()），CRUD 只 flush 不 commit。

    CRUD 层只自动填充 created_id/updated_id，不按这些字段过滤数据。
    数据权限由 Service 层负责 —— Service 层忘记过滤 = 越权风险。
    """

    def __init__(self, model: type[ModelType], auth: AuthSchema, db: AsyncSession) -> None:
        self.model = model
        self.auth = auth
        self.db = db

    # ── 辅助方法 ──────────────────────────────────────────────────────

    def _get_pk_col(self) -> ColumnElement:
        """获取模型的主键列。delete/set/restore/page 批量操作共用。"""
        mapper = sa_inspect(self.model)
        pk_cols = list(mapper.primary_key)
        if not pk_cols:
            raise CustomException(msg="模型缺少主键")
        if len(pk_cols) > 1:
            raise CustomException(msg="暂不支持复合主键操作")
        return pk_cols[0]

    @property
    def _supports_soft_delete(self) -> bool:
        # 判断模型是否有 is_deleted / deleted_time / deleted_id 三个字段
        return all(hasattr(self.model, attr) for attr in ("is_deleted", "deleted_time", "deleted_id"))

    def _soft_delete_values(self) -> dict[str, Any]:
        """返回 UPDATE 设置软删除字段所需的 values 字典。"""
        data: dict[str, Any] = {"is_deleted": True, "deleted_time": datetime.now(UTC)}
        if self.auth.user.id:
            data["deleted_id"] = self.auth.user.id
        return data

    # ── 查询 ──────────────────────────────────────────────────────────

    async def get(self, preload: list[str | Any] | None = None, include_deleted: bool = False, **kwargs) -> ModelType | None:
        """单条查询。**kwargs 按字段名 = 值传参，自动转 WHERE 条件。"""
        try:
            conditions = await self._build_conditions(include_deleted=include_deleted, **kwargs)
            sql = select(self.model).where(*conditions)
            for opt in self._loader_options(preload):
                sql = sql.options(opt)
            result: Result = await self.db.execute(sql)
            return result.scalars().first()
        except Exception as e:
            raise CustomException(msg=f"获取查询失败: {e!s}") from e

    async def get_or_404(
        self,
        id: int | None = None,
        msg: str = "该数据不存在",
        preload: list[str | Any] | None = None,
        out_schema: type[OutSchemaType] | None = None,
        include_deleted: bool = False,
        **kwargs,
    ) -> ModelType | OutSchemaType:
        """查不到直接抛异常。支持 id 快捷入参，也支持 **kwargs 传多个条件。"""
        if id is not None:
            kwargs["id"] = id
        obj = await self.get(preload=preload, include_deleted=include_deleted, **kwargs)
        if not obj:
            raise CustomException(msg=msg)
        return out_schema.model_validate(obj) if out_schema else obj

    async def exists(self, include_deleted: bool = False, **kwargs) -> bool:
        # 用 COUNT 代替 SELECT，避免加载整行数据和关联关系
        return await self.count(include_deleted=include_deleted, **kwargs) > 0

    async def count(self, include_deleted: bool = False, **kwargs) -> int:
        """统计行数。"""
        try:
            conditions = await self._build_conditions(include_deleted=include_deleted, **kwargs)
            count_sql = select(func.count()).select_from(self.model).where(*conditions)
            result: Result = await self.db.execute(count_sql)
            return result.scalar() or 0
        except Exception as e:
            raise CustomException(msg=f"统计失败: {e!s}") from e

    async def get_list(
        self,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
        preload: list[str | Any] | None = None,
        load_columns: list | None = None,
        include_deleted: bool = False,
    ) -> Sequence[ModelType]:
        """不分页的列表查询。"""
        try:
            conditions = await self._build_conditions(include_deleted=include_deleted, **(search or {}))
            order = order_by or [{"id": "asc"}]
            sql = select(self.model).where(*conditions).order_by(*self._parse_order(order))
            if load_columns:
                sql = sql.options(load_only(*load_columns))
            for opt in self._loader_options(preload):
                sql = sql.options(opt)
            result: Result = await self.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"列表查询失败: {e!s}") from e

    async def page(
        self,
        offset: int,
        limit: int,
        order_by: list[dict[str, str]],
        search: dict[str, Any] | None = None,
        out_schema: type[OutSchemaType] | None = None,
        preload: list[str | Any] | None = None,
        load_columns: list | None = None,
        include_deleted: bool = False,
    ) -> PageResultSchema[OutSchemaType] | PageResultSchema:
        """分页查询。COUNT + 数据分两趟查，COUNT 复用 WHERE 但不带 loading options。"""
        try:
            conditions = await self._build_conditions(include_deleted=include_deleted, **(search or {}))
            order = order_by or [{"id": "asc"}]

            pk = self._get_pk_col()  # COUNT 用主键列更精确

            data_sql = select(self.model).where(*conditions)
            if load_columns:
                data_sql = data_sql.options(load_only(*load_columns))
            for opt in self._loader_options(preload):
                data_sql = data_sql.options(opt)

            # 从 data_sql 提取 WHERE，构造独立的 COUNT 查询（去掉 loader option，避免 LEFT JOIN 开销）
            count_sql = select(func.count(pk)).select_from(self.model)
            where_clause = data_sql.whereclause
            if where_clause is not None:
                count_sql = count_sql.where(where_clause)

            total_result = await self.db.execute(count_sql)
            total = total_result.scalar() or 0

            result: Result = await self.db.execute(data_sql.order_by(*self._parse_order(order)).offset(offset).limit(limit))
            objs = result.scalars().all()

            items = [out_schema.model_validate(obj) for obj in objs] if out_schema else list(objs)

            return PageResultSchema(
                page_no=offset // limit + 1 if limit else 1,
                page_size=limit or 10,
                total=total,
                has_next=offset + limit < total,
                items=items,
            )
        except Exception as e:
            raise CustomException(msg=f"分页查询失败: {e!s}") from e

    # ── 写入 ──────────────────────────────────────────────────────────

    async def create(self, data: CreateSchemaType | dict[str, Any]) -> ModelType:
        """新增记录。"""
        try:
            obj_dict = data.model_dump(exclude_none=True) if isinstance(data, BaseModel) else cast("dict[str, Any]", data)
            obj = self.model(**obj_dict)

            user = self.auth.user
            if user.id:
                # 自动填充审计人，hasattr 兼容无审计字段的模型
                if hasattr(obj, "created_id"):
                    setattr(obj, "created_id", user.id)
                if hasattr(obj, "updated_id"):
                    setattr(obj, "updated_id", user.id)

            self.db.add(obj)
            await self.db.flush()
            await self.db.refresh(obj)

            preload_options = []
            mapper = sa_inspect(self.model)
            if hasattr(mapper, "relationships"):
                for rel_name in ("created_by", "updated_by"):
                    if rel_name in mapper.relationships:
                        preload_options.append(joinedload(getattr(self.model, rel_name)))
            if preload_options:
                result = await self.db.execute(
                    select(self.model).options(*preload_options).where(self._get_pk_col() == obj.id)
                )
                obj = result.scalar_one()

            return obj
        except Exception as e:
            raise CustomException(msg=f"创建失败: {e!s}") from e

    async def update(self, id: int, data: UpdateSchemaType | dict[str, Any]) -> ModelType:
        """更新记录。用 exclude_unset / exclude_none 准确表达前端意图。"""
        try:
            obj_dict = data.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}) if isinstance(data, BaseModel) else cast("dict[str, Any]", data)
            obj = await self.get(id=id)
            if not obj:
                raise CustomException(msg="更新对象不存在")

            # 更新操作自动更新 updated_id
            user = self.auth.user
            if user.id and hasattr(obj, "updated_id"):
                setattr(obj, "updated_id", user.id)

            for key, value in obj_dict.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.flush()
            await self.db.refresh(obj)

            preload_options = []
            mapper = sa_inspect(self.model)
            if hasattr(mapper, "relationships"):
                for rel_name in ("created_by", "updated_by"):
                    if rel_name in mapper.relationships:
                        preload_options.append(joinedload(getattr(self.model, rel_name)))
            if preload_options:
                result = await self.db.execute(
                    select(self.model).options(*preload_options).where(self._get_pk_col() == obj.id)
                )
                obj = result.scalar_one()

            return obj
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"更新失败: {e!s}") from e

    async def delete(self, ids: list[int]) -> None:
        """软删除优先，无软删除则物理删除。"""
        try:
            pk = self._get_pk_col()
            if self._supports_soft_delete:
                # 加 is_deleted=false() 条件，防止重复软删除（幂等）
                sql = update(self.model).where(pk.in_(ids)).where(
                    getattr(self.model, "is_deleted") == false()
                ).values(**self._soft_delete_values())
            else:
                sql = delete(self.model).where(pk.in_(ids))
            await self.db.execute(sql)
            await self.db.flush()
        except Exception as e:
            raise CustomException(msg=f"删除失败: {e!s}") from e

    async def clear(self) -> None:
        """清空整表。软删除模式下相当于"回收站清空"，只清理已删标记的记录。"""
        try:
            if self._supports_soft_delete:
                sql = update(self.model).where(
                    getattr(self.model, "is_deleted") == true()
                ).values(**self._soft_delete_values())
            else:
                sql = delete(self.model)
            await self.db.execute(sql)
            await self.db.flush()
        except Exception as e:
            raise CustomException(msg=f"清空失败: {e!s}") from e

    async def set(self, ids: list[int], include_deleted: bool = False, **kwargs) -> None:
        """批量更新。软删除模式下默认跳过已删除的记录。"""
        try:
            pk = self._get_pk_col()
            sql = update(self.model).where(pk.in_(ids))
            if self._supports_soft_delete and not include_deleted:
                sql = sql.where(getattr(self.model, "is_deleted") == false())
            sql = sql.values(**kwargs)
            await self.db.execute(sql)
            await self.db.flush()
        except Exception as e:
            raise CustomException(msg=f"批量更新失败: {e!s}") from e

    # ── 条件与排序 ────────────────────────────────────────────────────

    async def _build_conditions(self, include_deleted: bool = False, **kwargs) -> list[ColumnElement]:
        """根据 kwargs 动态拼接 WHERE 条件列表。

        值类型决定比较方式：
        - tuple     → 委托 _resolve_condition（like/in/between/date/null/比较操作符）
        - 其他      → 等值比较兜底（仅兼容 ``get(id=1)`` 等直接关键字传参）

        None / 空串的键值对跳过，不做条件。

        提示：分页/列表/统计查询走 ``search_to_dict`` 后 kwargs 值均为 tuple，
        由 Schema 层的 ``json_schema_extra={"q": "..."}`` 精确控制操作符。
        """
        conditions: list[ColumnElement] = []

        # 自动排除已删除记录（除非调用方明确要查询已删除数据）
        if hasattr(self.model, "is_deleted") and not include_deleted:
            conditions.append(getattr(self.model, "is_deleted") == false())

        from app.core.permission import Permission

        permission_condition = await Permission(self.model, self.auth, self.db)._permission_condition()
        if permission_condition is not None:
            conditions.append(permission_condition)

        for key, value in kwargs.items():
            if value is None or value == "":
                continue
            attr = getattr(self.model, key)
            if isinstance(value, tuple):
                conditions.extend(self._resolve_condition(attr, value))
            else:
                conditions.append(attr == value)
        return conditions

    @staticmethod
    def _resolve_condition(attr: ColumnElement, value: tuple) -> list[ColumnElement]:
        """元组条件 `(seq, val)` → SQLAlchemy condition。

        seq 支持：None / not None / date / month / like / in / between / 比较操作符。

        date 返回 [>=当天0:00, <第二天0:00) 的范围，
        month 返回 [>=1号0:00, <下月1号0:00) 的范围。
        """
        seq, val = value

        # 先处理不依赖 val 的 IS NULL / IS NOT NULL
        handlers: dict[str, Any] = {
            "None": lambda: [attr.is_(None)],
            "not None": lambda: [attr.isnot(None)],
        }
        if seq in handlers:
            return handlers[seq]()

        if val is None:
            return []

        if seq == "date":
            dt = datetime.strptime(val, "%Y-%m-%d")
            return [attr >= dt, attr < dt + timedelta(days=1)]
        if seq == "month":
            dt = datetime.strptime(val, "%Y-%m")
            next_month = dt.replace(year=dt.year + 1, month=1) if dt.month == 12 else dt.replace(month=dt.month + 1)
            return [attr >= dt, attr < next_month]
        if seq == "like":
            return [attr.like(f"%{val}%")]
        if seq == "in":
            if isinstance(val, (list, tuple, set)) and len(val) == 0:
                return [false()]  # 空集合查询 = 永假条件
            return [attr.in_(val)]
        if seq == "between" and isinstance(val, (list, tuple)) and len(val) == 2:
            return [attr.between(val[0], val[1])]

        method = _OPERATOR_MAP.get(seq)
        if method is not None:
            return [getattr(attr, method)(val)]
        return []

    def _parse_order(self, order: list[dict[str, str]]) -> list[ColumnElement]:
        """`[{"field": "asc|desc"}, ...]` → SQLAlchemy order_by 子句。"""
        columns: list[ColumnElement] = []
        for item in order:
            for field, direction in item.items():
                column = getattr(self.model, field)  # type: ignore[arg-type]
                columns.append(desc(column) if direction.lower() == "desc" else asc(column))
        return columns

    def _loader_options(self, preload: list[str | Any] | None = None) -> list[Any]:
        """将字符串预加载描述转为 SQLAlchemy loading options。

        - "user"       → joinedload（一对一/多对一）或 selectinload（一对多/多对多）
        - "user.dept"  → 嵌套加载（通过 .options() 链式组合）
        - 已存在 options 对象 → 原样追加

        自动为 created_by / updated_by 添加 joinedload（所有查询都 LEFT JOIN 用户表获取审计人）。
        """
        options: list[Any] = []
        if not preload:
            preload = []
        mapper = sa_inspect(self.model)
        processed_attrs = set()

        for opt in preload:
            if isinstance(opt, str):
                parts = opt.split(".")
                if len(parts) == 1:
                    attr_name = parts[0]
                    if attr_name in processed_attrs:
                        continue  # 跳过同层重复名称
                    processed_attrs.add(attr_name)
                    if not hasattr(self.model, attr_name):
                        continue  # 非模型属性，忽略
                    prop = mapper.relationships.get(attr_name)
                    if prop is None:
                        continue  # 列属性不支持 eager loading，忽略
                    attr = getattr(self.model, attr_name)
                    # 一对一/多对一用 joinedload（一条 SQL 完成），一对多/多对多用 selectinload（N+1 → 2 条 SQL）
                    if not prop.uselist:
                        options.append(joinedload(attr))
                    else:
                        options.append(selectinload(attr))
                else:
                    full_path = ".".join(parts)
                    if full_path in processed_attrs:
                        continue  # 跳过完全相同的嵌套路径
                    processed_attrs.add(full_path)
                    current_model = self.model
                    current_mapper = mapper
                    current_option = None
                    for part in parts:
                        if not hasattr(current_model, part):
                            break
                        attr = getattr(current_model, part)
                        prop = current_mapper.relationships.get(part)
                        if prop is None:
                            break  # 非关系属性中断链
                        loader = selectinload(attr) if prop.uselist else joinedload(attr)
                        # 嵌套加载通过 .options() 链式组合
                        if current_option is None:
                            current_option = loader
                        else:
                            current_option = current_option.options(loader)
                        current_model = prop.mapper.class_
                        current_mapper = sa_inspect(current_model)
                    if current_option is not None:
                        options.append(current_option)
            else:
                options.append(opt)

        # 自动预加载审计关系：常见列表页都要展示创建人/更新人，统一处理避免 N+1
        for audit_attr in ["created_by", "updated_by"]:
            if audit_attr not in processed_attrs and audit_attr in mapper.relationships:
                prop = mapper.relationships[audit_attr]
                if hasattr(self.model, audit_attr):
                    attr = getattr(self.model, audit_attr)
                    options.append(joinedload(attr))

        return options
