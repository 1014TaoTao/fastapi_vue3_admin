import asyncio
import json
from typing import Any

from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import EnvironmentEnum
from app.config.path_conf import ALEMBIC_VERSION_DIR, BASE_DIR, SCRIPT_DIR, STATIC_DIR
from app.config.setting import settings
from app.core.base_model import MappedBase
from app.core.database import async_db_session, async_engine, create_tables
from app.core.logger import logger
from app.modules.system.dept.model import DeptModel
from app.modules.system.dict.model import DictDataModel, DictTypeModel
from app.modules.system.menu.model import MenuModel
from app.modules.system.params.model import ParamsModel
from app.modules.system.role.model import RoleModel
from app.modules.system.user.model import UserModel, UserRolesModel
from app.modules.system.versions.model import VersionModel
from app.modules.task.cronjob.node.model import NodeModel
from app.modules.task.storage.node.model import StorageNodeModel
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
        NodeModel,
        StorageNodeModel,
    ]

    # 树形模型：JSON 含嵌套 children，需递归创建对象
    _RECURSIVE_TABLES: set[str] = {"sys_menu", "sys_dept"}

    async def init_db(self) -> None:
        """应用数据库迁移并导入种子数据（迁移成功即证明连接正常，失败时异常上抛）"""
        await self.__apply_migrations()

        async with async_db_session() as session, session.begin():
            await self.__init_data(session)

        # 内置本地存储源的根目录（种子节点 host 指向 static/upload），保证开箱可浏览
        (STATIC_DIR / "upload").mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def __apply_migrations() -> None:
        """将数据库 schema 带到模型定义的最新的版本（开源项目要求任意方言开箱即用）。"""
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
        skipped: list[str] = []
        for model in self.prepare_init_models:
            table_name = model.__tablename__

            data = self.__load_json(table_name)
            if not data:
                logger.info(f"⏭️  跳过 {table_name} 表，无初始化数据")
                continue

            # 已有数据则跳过（汇总到循环结束后一次输出，避免每次启动刷 9 行）
            count = await db.execute(select(func.count()).select_from(model))
            if count.scalar():
                skipped.append(table_name)
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

        if skipped:
            logger.info(f"⏭️  {len(skipped)} 张表已有数据，跳过初始化：{', '.join(skipped)}")

    @staticmethod
    async def __create_dict_data_objs(db: AsyncSession, data: list[dict]) -> list[DictDataModel]:
        """字典数据种子：dict_type_id 通过查询库内字典类型解析。"""
        type_names = {item.get("dict_type") for item in data if item.get("dict_type")}
        result = await db.execute(
            select(DictTypeModel.dict_type, DictTypeModel.id).where(
                DictTypeModel.dict_type.in_(type_names)
            )
        )
        # Row[Tuple[str, int]] 静态类型上不是双元素 (key, value) 元组，dict(rows) 会被类型检查器拒绝；
        # 用下标显式拆出 (dict_type, id) 再构造，运行行为不变且类型清晰
        id_map: dict[str, int] = {row[0]: row[1] for row in result.all()}

        objs: list[DictDataModel] = []
        for item in data:
            dict_type = item.get("dict_type")
            if not isinstance(dict_type, str):  # 与 type_names 的 truthy 过滤一致，同时收窄类型
                continue
            dict_type_id = id_map.get(dict_type)
            if dict_type_id is None:
                logger.warning(f"⚠️  未找到字典类型 {dict_type}，跳过")
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
