import json
from typing import Any

from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import RedisInitKeyConfig
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.database import async_db_session
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD
from app.utils.common_util import search_to_dict

from .crud import DictDataCRUD, DictTypeCRUD
from .schema import (
    DictDataCreateSchema,
    DictDataOutSchema,
    DictDataQueryParam,
    DictDataUpdateSchema,
    DictTypeCreateSchema,
    DictTypeOutSchema,
    DictTypeQueryParam,
    DictTypeUpdateSchema,
)


class DictTypeService:
    """字典类型管理服务

    设计：实例方法承载「当前用户上下文 (auth)」，``redis`` 仍是方法参数
    （因为不是每个端点都用到）。调用方写法由 ``XxxService.method_service(auth=...)``
    改为 ``XxxService(auth).method(...)``。
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> DictTypeOutSchema:
        """获取数据字典类型详情

        参数:
        - id (int): 数据字典类型ID

        返回:
        - DictTypeOutSchema: 字典类型响应模型
        """
        obj = await DictTypeCRUD(self.auth, self.db).get_or_404(id=id)
        return DictTypeOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: DictTypeQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[DictTypeOutSchema]:
        """获取数据字典类型列表

        参数:
        - search (DictTypeQueryParam | None): 搜索条件模型
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - list[DictTypeOutSchema]: 字典类型响应模型列表
        """
        obj_list = await DictTypeCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by)
        return [DictTypeOutSchema.model_validate(obj) for obj in obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: DictTypeQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> PageResultSchema[DictTypeOutSchema]:
        """分页查询字典类型（数据库 OFFSET/LIMIT）。

        参数:
        - page_no (int): 页码（从 1 开始）
        - page_size (int): 每页条数
        - search (DictTypeQueryParam | None): 查询条件
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - PageResultSchema[DictTypeOutSchema]: 分页结果
        """
        offset = (page_no - 1) * page_size
        return await DictTypeCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            out_schema=DictTypeOutSchema,
        )

    async def create(self, redis: Redis, data: DictTypeCreateSchema) -> DictTypeOutSchema:
        """创建数据字典类型

        参数:
        - redis (Redis): Redis客户端
        - data (DictTypeCreateSchema): 数据字典类型创建模型

        返回:
        - DictTypeOutSchema: 字典类型响应模型
        """
        exist_obj = await DictTypeCRUD(self.auth, self.db).get(dict_name=data.dict_name)
        if exist_obj:
            raise CustomException(msg="创建失败，该数据已存在")
        obj = await DictTypeCRUD(self.auth, self.db).create(data=data)

        new_obj_dict = DictTypeOutSchema.model_validate(obj)

        redis_key = f"{RedisInitKeyConfig.SYSTEM_DICT.key}:1:{data.dict_type}"

        try:
            await RedisCURD(redis).set(
                key=redis_key,
                value="[]",
                expire=None,
            )
            logger.info(f"创建字典类型成功: {new_obj_dict}")
        except Exception as e:
            logger.error(f"创建字典类型失败: {e}")
            raise CustomException(msg="同步字典类型缓存失败") from e

        return new_obj_dict

    async def update(
        self,
        redis: Redis,
        id: int,
        data: DictTypeUpdateSchema,
    ) -> DictTypeOutSchema:
        """更新数据字典类型

        参数:
        - redis (Redis): Redis客户端
        - id (int): 数据字典类型ID
        - data (DictTypeUpdateSchema): 数据字典类型更新模型

        返回:
        - DictTypeOutSchema: 字典类型响应模型
        """
        exist_obj = await DictTypeCRUD(self.auth, self.db).get_or_404(id=id, msg="更新失败，该数据不存在")
        if exist_obj.dict_name != data.dict_name:
            raise CustomException(msg="更新失败，数据字典类型名称不可以修改")

        # 如果字典类型修改或状态变更，则修改对应字典数据的类型和状态
        if exist_obj.dict_type != data.dict_type or exist_obj.status != data.status:
            # 级联批量更新关联字典数据：先取类型下未删除的数据行，再走 CRUDBase.set
            # （get_list/set 自动带软删过滤 + 数据权限，不再直改软删记录）
            data_crud = DictDataCRUD(self.auth, self.db)
            rows = await data_crud.get_list(search={"dict_type": exist_obj.dict_type})
            if rows:
                update_values: dict[str, Any] = {"status": data.status}
                if exist_obj.dict_type != data.dict_type:
                    update_values["dict_type"] = data.dict_type
                await data_crud.set(ids=[row.id for row in rows], **update_values)

        obj = await DictTypeCRUD(self.auth, self.db).update(id=id, data=data)

        new_obj_dict = DictTypeOutSchema.model_validate(obj)

        redis_key = f"{RedisInitKeyConfig.SYSTEM_DICT.key}:1:{data.dict_type}"
        try:
            # 获取当前字典类型的所有字典数据，确保包含最新状态
            dict_data_list = await DictDataCRUD(self.auth, self.db).get_list(search={"dict_type": data.dict_type})
            dict_data = [DictDataOutSchema.model_validate(row).model_dump(mode="json") for row in dict_data_list if row]

            value = json.dumps(dict_data, ensure_ascii=False)
            await RedisCURD(redis).set(
                key=redis_key,
                value=value,
                expire=None,
            )
            logger.info(f"更新字典类型成功并刷新缓存: {new_obj_dict}")
        except Exception as e:
            logger.error(f"更新字典类型缓存失败: {e}")
            raise CustomException(msg="同步字典类型缓存失败") from e

        return new_obj_dict

    async def delete(self, redis: Redis, ids: list[int]) -> None:
        """删除数据字典类型

        参数:
        - redis (Redis): Redis客户端
        - ids (list[int]): 数据字典类型ID列表

        返回:
        - None
        """
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        existing = await DictTypeCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        existing_map = {obj.id: obj for obj in existing}
        # 收集所有 dict_type 去重后批量查询是否有字典数据
        dict_types = {obj.dict_type for obj in existing if obj.id in ids}
        dict_type_has_data: set[str] = set()
        for dt in dict_types:
            if await DictDataCRUD(self.auth, self.db).get_list(search={"dict_type": dt}):
                dict_type_has_data.add(dt)
        for nid in ids:
            if nid not in existing_map:
                raise CustomException(msg="删除失败，该数据不存在")
            exist_obj = existing_map[nid]
            if exist_obj.dict_type in dict_type_has_data:
                raise CustomException(msg="删除失败，该数据字典类型下存在字典数据")
        # 验证通过后统一删除 Redis 缓存
        existing_dict_types = {obj.dict_type for obj in existing if obj.id in ids}
        for dt in existing_dict_types:
            redis_key = f"{RedisInitKeyConfig.SYSTEM_DICT.key}:1:{dt}"
            try:
                await RedisCURD(redis).delete(redis_key)
                logger.info(f"删除字典类型缓存: {dt}")
            except Exception as e:
                logger.error(f"删除字典类型缓存失败: {e}")
                raise CustomException(msg="同步删除字典缓存失败") from e
        await DictTypeCRUD(self.auth, self.db).delete(ids=ids)

    async def set_available(self, data: BatchSetAvailable) -> None:
        """设置数据字典类型状态

        参数:
        - data (BatchSetAvailable): 批量设置状态模型

        返回:
        - None
        """
        await DictTypeCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

class DictDataService:
    """字典数据管理服务

    设计同 DictTypeService：实例方法 + ``__init__(auth)``。
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> DictDataOutSchema:
        """获取数据字典数据详情

        参数:
        - id (int): 数据字典数据ID

        返回:
        - DictDataOutSchema: 字典数据响应模型
        """
        obj = await DictDataCRUD(self.auth, self.db).get_or_404(id=id)
        return DictDataOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: DictDataQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[DictDataOutSchema]:
        """获取数据字典数据列表

        参数:
        - search (DictDataQueryParam | None): 搜索条件模型
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - list[DictDataOutSchema]: 字典数据响应模型列表
        """
        obj_list = await DictDataCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by)
        return [DictDataOutSchema.model_validate(obj) for obj in obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: DictDataQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> PageResultSchema[DictDataOutSchema]:
        """分页查询字典数据（数据库 OFFSET/LIMIT）。

        参数:
        - page_no (int): 页码（从 1 开始）
        - page_size (int): 每页条数
        - search (DictDataQueryParam | None): 查询条件
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - PageResultSchema[DictDataOutSchema]: 分页结果
        """
        offset = (page_no - 1) * page_size
        return await DictDataCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            out_schema=DictDataOutSchema,
        )

    @staticmethod
    async def init_cache(redis: Redis) -> None:
        """应用初始化: 获取所有字典类型对应的字典数据信息并按租户缓存（无 auth）。

        参数:
        - redis (Redis): Redis客户端

        返回:
        - None
        """
        try:
            async with async_db_session() as session, session.begin():
                init_auth = AuthSchema()
                obj_list = await DictTypeCRUD(init_auth, session).get_list()
                if not obj_list:
                    logger.warning("未找到任何字典类型数据")
                    return

                for obj in obj_list:
                    dict_type = obj.dict_type
                    try:
                        dict_data_list = await DictDataCRUD(init_auth, session).get_list(search={"dict_type": dict_type})
                        dict_data = [DictDataOutSchema.model_validate(row).model_dump(mode="json") for row in dict_data_list if row]
                        redis_key = f"{RedisInitKeyConfig.SYSTEM_DICT.key}:1:{dict_type}"
                        value = json.dumps(dict_data, ensure_ascii=False)
                        await RedisCURD(redis).set(
                            key=redis_key,
                            value=value,
                            expire=None,
                        )
                    except Exception as e:
                        logger.error(f"❌ 初始化字典数据失败 [{dict_type}]: {e}")

        except Exception as e:
            logger.error(f"❌️ 字典初始化过程发生错误: {e}")
            raise CustomException(msg="字典数据初始化失败") from e

    @staticmethod
    async def get_init_cache(redis: Redis, dict_type: str) -> list[dict]:
        """从缓存获取字典数据列表信息（无 auth）。

        参数:
        - redis (Redis): Redis客户端
        - dict_type (str): 字典类型

        返回:
        - list[dict]: 字典数据列表
        """

        def _parse(data: str | list | None) -> list[dict] | None:
            """尝试反序列化 Redis 返回的字典缓存数据"""
            if data is None:
                return None
            if isinstance(data, list):
                return data
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return None

        try:
            redis_key = f"{RedisInitKeyConfig.SYSTEM_DICT.key}:1:{dict_type}"
            obj_list_dict = await RedisCURD(redis).get(redis_key)

            result = _parse(obj_list_dict)
            if result is not None:
                return result

            # 缓存未命中或格式异常，重新初始化
            logger.warning(f"字典缓存未命中或格式异常，重新初始化缓存: {dict_type}")
            await DictDataService.init_cache(redis)
            obj_list_dict = await RedisCURD(redis).get(redis_key)

            result = _parse(obj_list_dict)
            if result is None:
                raise CustomException(msg="该数据不存在")
            return result
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"获取字典缓存失败: {e!s}")
            raise CustomException(msg="获取字典数据失败") from e

    async def _refresh_dict_cache(self, redis: Redis, dict_type: str) -> None:
        """刷新指定字典类型的 Redis 缓存

        从数据库拉取全量数据，序列化后写入 Redis。

        参数:
        - redis (Redis): Redis 客户端
        - dict_type (str): 字典类型
        """
        redis_key = f"{RedisInitKeyConfig.SYSTEM_DICT.key}:1:{dict_type}"
        dict_data_list = await DictDataCRUD(self.auth, self.db).get_list(search={"dict_type": dict_type})
        dict_data = [DictDataOutSchema.model_validate(row).model_dump(mode="json") for row in dict_data_list if row]
        value = json.dumps(dict_data, ensure_ascii=False)
        await RedisCURD(redis).set(key=redis_key, value=value, expire=None)

    async def create(self, redis: Redis, data: DictDataCreateSchema) -> DictDataOutSchema:
        """创建数据字典数据

        参数:
        - redis (Redis): Redis客户端
        - data (DictDataCreateSchema): 数据字典数据创建模型

        返回:
        - DictDataOutSchema: 字典数据响应模型
        """
        # 检查相同字典类型下dict_label是否已存在
        exist_label_obj = await DictDataCRUD(self.auth, self.db).get(dict_type=data.dict_type, dict_label=data.dict_label)
        if exist_label_obj:
            raise CustomException(msg=f'创建失败，该字典类型下的字典标签"{data.dict_label}"已存在')

        # 检查相同字典类型下dict_value是否已存在
        exist_value_obj = await DictDataCRUD(self.auth, self.db).get(dict_type=data.dict_type, dict_value=data.dict_value)
        if exist_value_obj:
            raise CustomException(msg=f'创建失败，该字典类型下的字典键值"{data.dict_value}"已存在')

        obj = await DictDataCRUD(self.auth, self.db).create(data=data)

        try:
            await self._refresh_dict_cache(redis, data.dict_type)
            logger.info(f"创建字典数据写入缓存成功: {obj}")
        except Exception as e:
            logger.error(f"创建字典数据写入缓存失败: {e}")
            raise CustomException(msg="同步字典数据缓存失败") from e

        return DictDataOutSchema.model_validate(obj)

    async def update(
        self,
        redis: Redis,
        id: int,
        data: DictDataUpdateSchema,
    ) -> DictDataOutSchema:
        """更新数据字典数据

        参数:
        - redis (Redis): Redis客户端
        - id (int): 数据字典数据ID
        - data (DictDataUpdateSchema): 数据字典数据更新模型

        返回:
        - DictDataOutSchema: 字典数据响应模型
        """
        exist_obj = await DictDataCRUD(self.auth, self.db).get_or_404(id=id, msg="更新失败，该数据不存在")

        # 检查相同字典类型下dict_label是否已存在（排除当前记录）
        if exist_obj.dict_label != data.dict_label:
            exist_label_obj = await DictDataCRUD(self.auth, self.db).get(dict_type=data.dict_type, dict_label=data.dict_label)
            if exist_label_obj:
                raise CustomException(msg=f'更新失败，该字典类型下的字典标签"{data.dict_label}"已存在')

        # 检查相同字典类型下dict_value是否已存在（排除当前记录）
        if exist_obj.dict_value != data.dict_value:
            exist_value_obj = await DictDataCRUD(self.auth, self.db).get(dict_type=data.dict_type, dict_value=data.dict_value)
            if exist_value_obj:
                raise CustomException(msg=f'更新失败，该字典类型下的字典键值"{data.dict_value}"已存在')

        # 如果字典类型变更，仅刷新旧类型缓存，不联动字典类型状态
        if exist_obj.dict_type != data.dict_type:
            dict_type = await DictTypeCRUD(self.auth, self.db).get(dict_type=exist_obj.dict_type)
            if dict_type:
                try:
                    await self._refresh_dict_cache(redis, dict_type.dict_type)
                except Exception as e:
                    logger.error(f"刷新旧字典缓存失败: {e}")
                    raise CustomException(msg="同步旧字典数据缓存失败") from e

        obj = await DictDataCRUD(self.auth, self.db).update(id=id, data=data)

        # 刷新新/当前字典类型缓存（仅一次）
        try:
            await self._refresh_dict_cache(redis, data.dict_type)
            logger.info(f"更新字典数据写入缓存成功: {obj}")
        except Exception as e:
            logger.error(f"更新字典数据写入缓存失败: {e}")
            raise CustomException(msg="同步字典数据缓存失败") from e

        return DictDataOutSchema.model_validate(obj)

    async def delete(self, redis: Redis, ids: list[int]) -> None:
        """删除数据字典数据

        参数:
        - redis (Redis): Redis客户端
        - ids (list[int]): 数据字典数据ID列表

        返回:
        - None
        """
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        existing = await DictDataCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        existing_map = {obj.id: obj for obj in existing}
        for nid in ids:
            if nid not in existing_map:
                raise CustomException(msg="删除失败，该数据不存在")
        # 按 dict_type 分组，每组的缓存只刷新一次
        type_groups: dict[str, list[int]] = {}
        for obj in existing:
            if obj.id in ids:
                type_groups.setdefault(obj.dict_type, []).append(obj.id)
        for dt in type_groups:
            try:
                await self._refresh_dict_cache(redis, dt)
                logger.info(f"删除字典数据并刷新缓存: dict_type={dt}")
            except Exception as e:
                logger.error(f"删除字典数据刷新缓存失败: {e}")
                raise CustomException(msg="同步删除字典数据缓存失败") from e
        await DictDataCRUD(self.auth, self.db).delete(ids=ids)

    async def set_available(self, data: BatchSetAvailable) -> None:
        """设置数据字典数据状态

        参数:
        - data (BatchSetAvailable): 批量设置状态模型

        返回:
        - None
        """
        await DictDataCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)
