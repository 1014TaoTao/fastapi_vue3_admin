"""迁移一致性守卫 —— create_all 自举产物必须与模型 metadata 零漂移。

双轨制风险：新装用户走 create_all + stamp head 路径，存量用户走 alembic upgrade 路径。
若模型与自举产物漂移，两条路径会产出不同 schema 且无人发现（dev 启动时的自动迁移
只是隐式守卫，仅在开发者本机生效）。

覆盖范围说明：此处校验 SQLite 方言下 create_all 渲染产物 ≡ metadata；
MySQL 方言的 DDL 渲染差异由 dev 启动时的自动迁移（autogen 零差异检查）承担。
"""

import asyncio

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.config.path_conf import ALEMBIC_VERSION_DIR, BASE_DIR


def test_bootstrap_matches_metadata(test_client: TestClient, versions_before_layout: frozenset[str]) -> None:
    """守卫一：布局阶段不得产出迁移文件；守卫二：自举库与模型零漂移。"""
    cfg = Config(str(BASE_DIR / "alembic.ini"))

    # 守卫一：TestClient 布局（init_db）期间，dev 自动迁移不得向仓库 versions/ 写入文件。
    # 布局阶段产出 = create_all 产物与 metadata 存在漂移（被 dev autogen 消化），属污染信号。
    leaked = {p.name for p in ALEMBIC_VERSION_DIR.glob("*.py")} - versions_before_layout
    assert not leaked, f"测试布局阶段产出迁移文件（模型与自举库漂移）: {sorted(leaked)}"

    # 守卫二：显式跑一次 autogenerate，必须零产出（验证布局后的库 ≡ 模型，
    # 同时兜底布局阶段 autogen 失败被 warning 吞掉、库未真正对齐的场景）
    asyncio.run(asyncio.to_thread(command.revision, cfg, autogenerate=True, message="migration-guard"))
    produced = {p.name for p in ALEMBIC_VERSION_DIR.glob("*.py")} - versions_before_layout
    for name in produced:  # 清理守卫自身产物，避免污染仓库
        (ALEMBIC_VERSION_DIR / name).unlink()
    assert not produced, f"autogenerate 检出漂移并产出迁移文件: {sorted(produced)}"
