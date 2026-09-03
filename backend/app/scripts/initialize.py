import asyncio
import json
from typing import Any

from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.dept.model import DeptModel
from app.api.v1.module_system.dict.model import DictDataModel, DictTypeModel
from app.api.v1.module_system.menu.model import MenuModel
from app.api.v1.module_system.params.model import ParamsModel
from app.api.v1.module_system.role.model import RoleModel
from app.api.v1.module_system.user.model import UserModel, UserRolesModel
from app.api.v1.module_system.versions.model import VersionModel
from app.common.enums import EnvironmentEnum
from app.config.path_conf import ALEMBIC_VERSION_DIR, BASE_DIR, SCRIPT_DIR
from app.config.setting import settings
from app.core.base_model import MappedBase
from app.core.database import async_db_session, async_engine, check_db, create_tables
from app.core.logger import logger
from app.utils.import_util import ImportUtil

# 导入全部模型：与 alembic env.py 保持一致，确保全局 MapperRegistry 的 FK 引用可完整解析
ImportUtil.find_models(MappedBase)


class InitializeData:
    """初始化数据库和基础数据"""

    # 按依赖关系排序：先基础表，再关联表
    prepare_init_models: list[type] = [
        MenuModel,
        DeptModel,
        ParamsModel,
        RoleModel,
        DictTypeModel,
        DictDataModel,
        UserModel,
        UserRolesModel,
        VersionModel,
    ]

    # 树形模型：JSON 含嵌套 children，需递归创建对象
    _RECURSIVE_TABLES: set[str] = {"sys_menu", "sys_dept"}

    async def init_db(self) -> None:
        """应用数据库迁移并导入种子数据"""
        await check_db()
        await self.__apply_migrations()

        async with async_db_session() as session, session.begin():
            await self.__init_data(session)

    @staticmethod
    async def __apply_migrations() -> None:
        """将数据库 schema 带到模型定义的最新的版本（开源项目要求任意方言开箱即用）。

        - 空库（哨兵表不存在）：按 ORM metadata create_all 直接建全表——方言无关、模型即真源，
          使 docker compose / 本地首启 / CI 无需任何人工 baseline 迁移；若仓库已有迁移历史，
          随后 stamp head 标记为最新，保证后续增量迁移能对自举库正确应用。
        - 非空库：alembic upgrade head 执行增量迁移，存量环境的 schema 演进必须走入库+审查的迁移文件。
        - dev 环境：额外自动 autogenerate（模型有变更则生成迁移文件）并应用，实现零操作迁移；
          自动生成的迁移若含破坏性 DROP 操作，则中止应用并提示人工处理。

        env.py 内部使用 asyncio.run，alembic 命令需在独立线程中执行，避免与当前事件循环冲突。
        """
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))

        # 以 sys_menu 作为空库哨兵（按依赖排序最先建表），它不存在即视为全新空库
        async with async_engine.connect() as conn:
            has_sentinel = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table(MenuModel.__tablename__))
        empty_db = not has_sentinel

        if empty_db:
            await create_tables()
            if any(p.name != "__init__.py" for p in ALEMBIC_VERSION_DIR.glob("*.py")):
                # 仓库已有迁移历史：标记为 head，保证后续增量迁移能对自举库正确应用
                await asyncio.to_thread(command.stamp, alembic_cfg, "head")
                logger.info("✅ 空库：已按模型创建全表结构，并标记迁移历史为 head")
            else:
                logger.info("✅ 空库：已按模型创建全表结构（仓库暂无迁移历史，跳过 stamp）")
        else:
            # 先把数据库带到最新版本，否则 autogenerate 会因
            # "Target database is not up to date" 无法对比模型与库结构
            await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
            logger.info("✅ 数据库迁移已应用（alembic upgrade head）")

        # dev 环境：模型有变更时自动生成迁移文件（无变更时 env.py 的 process_revision_directives 会拦截，不产出文件）
        if settings.ENVIRONMENT == EnvironmentEnum.DEV:
            autogen = await asyncio.to_thread(InitializeData.__autogen_migration, alembic_cfg)
            if autogen:
                # 生成了新的迁移文件，应用之
                await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
                logger.info("✅ dev 自动生成的迁移已应用（检测到模型变更）")
            elif autogen is False:
                # 仅"无模型变更"才打此日志；失败/拦截（None）已由 warning/error 说明，不再输出易误导的 info
                logger.info("✅ dev 环境自动迁移检查完成（模型无变更）")

    @staticmethod
    def __autogen_migration(alembic_cfg) -> bool | None:
        """dev 环境自动生成迁移文件。

        返回:
        - True: 生成了新的迁移文件（需再次 upgrade 应用）
        - False: 模型无变更（env.py 拦截空迁移，未产出文件）
        - None: 生成失败，或含破坏性 DROP 被拦截删除（warning/error 已说明原因）
        """
        import re
        from datetime import datetime

        from alembic import command

        before = set(ALEMBIC_VERSION_DIR.glob("*.py"))
        try:
            command.revision(alembic_cfg, autogenerate=True, message=f"自动迁移-{datetime.now():%m%d%H%M}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"⚠️ 自动生成迁移失败（{e}），跳过自动生成，仅应用已有迁移")
            return None

        new_files = set(ALEMBIC_VERSION_DIR.glob("*.py")) - before
        if not new_files:
            return False

        # drop_* 覆盖 drop_table/drop_column/drop_index/drop_constraint 等；op.execute 拦手写 DROP 语句
        dangerous = re.compile(r"""^\s*op\.drop_\w+\(|op\.execute\(["'].*\bDROP\b""", re.MULTILINE)
        for path in new_files:
            content = path.read_text(encoding="utf-8")
            # 仅检查 upgrade 段（downgrade 中的 DROP 是正常回滚逻辑）
            upgrade_part = content.split("def upgrade", 1)[-1].split("def downgrade", 1)[0]
            if dangerous.search(upgrade_part):
                path.unlink()
                logger.error(f"🚫 自动迁移 {path.name} 含破坏性 DROP 操作，已删除并中止自动应用")
                logger.error("请手动执行 python main.py revision --env=dev 生成迁移，审查确认后 python main.py upgrade --env=dev")
                return None
        return True

    async def __init_data(self, db: AsyncSession) -> None:
        """按依赖顺序初始化各表种子数据（表已有数据则整体跳过，实现幂等）"""
        for model in self.prepare_init_models:
            table_name = model.__tablename__

            data = self.__load_json(table_name)
            if not data:
                logger.info(f"⏭️  跳过 {table_name} 表，无初始化数据")
                continue

            # 已有数据则跳过
            count = await db.execute(select(func.count()).select_from(model))
            if count.scalar():
                logger.info(f"⏭️  跳过 {table_name} 表数据初始化（表已有数据）")
                continue

            try:
                if table_name in self._RECURSIVE_TABLES:
                    objs = self.__create_objects_with_children(data, model)
                elif table_name == "sys_dict_data":
                    objs = await self.__create_dict_data_objs(db, data)
                else:
                    objs = [model(**item) for item in data]

                if objs:
                    db.add_all(objs)
                    await db.flush()
                    logger.info(f"✅️ 已向 {table_name} 写入初始化数据")
                else:
                    logger.info(f"⏭️  跳过 {table_name} 表数据初始化（无有效数据）")

            except Exception:
                logger.error(f"❌️ 初始化 {table_name} 表数据失败")
                raise

    @staticmethod
    async def __create_dict_data_objs(db: AsyncSession, data: list[dict]) -> list[DictDataModel]:
        """字典数据种子：dict_type_id 通过查询库内字典类型解析。

        不依赖本次运行新建的对象——即使 sys_dict_type 早在之前的初始化中已入库、
        本次仅补录字典数据，外键也能正确解析。
        """
        type_names = {item.get("dict_type") for item in data if item.get("dict_type")}
        result = await db.execute(
            select(DictTypeModel.dict_type, DictTypeModel.id).where(
                DictTypeModel.dict_type.in_(type_names)
            )
        )
        id_map = dict(result.all())

        objs: list[DictDataModel] = []
        for item in data:
            dict_type_id = id_map.get(item.get("dict_type"))
            if dict_type_id is None:
                logger.warning(f"⚠️  未找到字典类型 {item.get('dict_type')}，跳过")
                continue
            item["dict_type_id"] = dict_type_id
            objs.append(DictDataModel(**item))
        return objs

    @staticmethod
    def __create_objects_with_children(data: list[dict], model_class: type) -> list:
        """递归创建树形模型实例，处理嵌套 children 并注入 parent_id"""

        def _create(obj_data: dict) -> Any:
            children_data = obj_data.pop("children", [])
            obj = model_class(**obj_data)

            # 子节点通过 relationship 自动设置 parent_id
            if children_data:
                obj.children = [_create(child) for child in children_data]

            return obj

        return [_create(item) for item in data]

    @staticmethod
    def __load_json(filename: str) -> list[dict]:
        """读取并解析种子数据 JSON 文件（不存在则返回空列表）"""
        json_path = SCRIPT_DIR / f"{filename}.json"
        if not json_path.exists():
            return []

        try:
            with open(json_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"❌️ 解析 {json_path} 失败: {e!s}")
            raise
        except Exception as e:
            logger.error(f"❌️ 读取 {json_path} 失败: {e!s}")
            raise
