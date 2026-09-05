import os
from typing import Annotated

import typer
import uvicorn
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from typer.main import Typer

from app.common.enums import EnvironmentEnum
from app.config.setting import settings
from app.init_app import create_app
from app.utils.banner import worship

fastapiadmin_cli: Typer = typer.Typer()
alembic_cfg: Config = Config(file_="alembic.ini")
app: FastAPI = create_app()

@fastapiadmin_cli.command(
    name="run",
    help="启动 FastapiAdmin 服务, 运行 uv run main.py run --env=dev 不加参数默认 dev 环境",
)
def run(
    env: Annotated[EnvironmentEnum, typer.Option("--env", help="运行环境 (dev, prod)")] = EnvironmentEnum.DEV,
) -> None:
    """按指定环境加载配置并启动 Uvicorn（开发环境开启 reload）。

    参数:
    - env (EnvironmentEnum): 运行环境，对应 `--env`。

    返回:
    - None
    """
    # 设置环境变量：本进程的 settings 已在模块导入时固化，此处由 uvicorn 子进程继承
    # ENVIRONMENT 后重新 import main，使 --env 真正生效（revision/upgrade 另用 cache_clear 处理）
    os.environ["ENVIRONMENT"] = env.value

    typer.secho(
        message=f"{worship()}",
        fg=typer.colors.GREEN,
    )

    # 启动uvicorn服务（传 import string 而非实例：reload/多 worker 模式要求子进程重新 import，
    # 且 os.environ 的环境设置由子进程继承后，settings 才能按 --env 正确加载）
    uvicorn.run(
        app=app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=env.value == EnvironmentEnum.DEV.value,
        workers=settings.WORKERS if env.value == EnvironmentEnum.PROD.value else 1,
        factory=True,
        log_config=None,
        timeout_graceful_shutdown=5,
    )


@fastapiadmin_cli.command(
    name="revision",
    help="生成新的 Alembic 迁移脚本, 运行 python main.py revision --env=dev",
)
def revision(
    env: Annotated[EnvironmentEnum, typer.Option("--env", help="运行环境 (dev, prod)")] = EnvironmentEnum.DEV,
) -> None:
    """使用 Alembic 自动生成迁移脚本（autogenerate）。

    参数:
    - env (EnvironmentEnum): 运行环境，用于加载对应数据库模型元数据。

    返回:
    - None
    """
    os.environ["ENVIRONMENT"] = env.value
    from app.config.setting import get_settings

    get_settings.cache_clear()
    command.revision(config=alembic_cfg, autogenerate=True, message="迁移脚本")
    typer.echo(message="迁移脚本已生成")


@fastapiadmin_cli.command(
    name="upgrade",
    help="应用最新的 Alembic 迁移, 运行 python main.py upgrade --env=dev",
)
def upgrade(
    env: Annotated[EnvironmentEnum, typer.Option("--env", help="运行环境 (dev, prod)")] = EnvironmentEnum.DEV,
) -> None:
    """将数据库升级到 Alembic 最新版本（head）。

    参数:
    - env (EnvironmentEnum): 运行环境。

    返回:
    - None
    """
    os.environ["ENVIRONMENT"] = env.value
    from app.config.setting import get_settings

    get_settings.cache_clear()
    command.upgrade(config=alembic_cfg, revision="head")
    typer.echo(message="所有迁移已应用。")


if __name__ == "__main__":
    fastapiadmin_cli()
