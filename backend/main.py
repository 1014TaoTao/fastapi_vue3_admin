# -*- coding: utf-8 -*-

import os
import uvicorn
import typer
from fastapi import FastAPI
from alembic import command
from alembic.config import Config

from app.common.enums import EnvironmentEnum

shell_app = typer.Typer()

# 初始化 Alembic 配置
alembic_cfg = Config("alembic.ini")


def create_app() -> FastAPI:
    from app.config.setting import settings
    from app.plugin.init_app import (
        register_middlewares,
        register_exceptions,
        register_routers,
        register_files,
        reset_api_docs,
        lifespan,
    )

    # 创建FastAPI应用
    app = FastAPI(**settings.FASTAPI_CONFIG, lifespan=lifespan)

    # 注册异常处理器
    register_exceptions(app)
    # 注册中间件
    register_middlewares(app)
    # 注册路由
    register_routers(app)
    # 注册静态文件
    register_files(app)
    # 重设API文档
    reset_api_docs(app)

    return app


@shell_app.command()
# def run(env: EnvironmentEnum = typer.Option(EnvironmentEnum.DEV, "--env", help="运行环境 (dev, prod)")):
def run(env: str = typer.Option("dev", "--env", help="运行环境 (dev, prod)")):
    typer.echo("项目启动中..")
    # 设置环境变量
    # os.environ["ENVIRONMENT"] = env.value
    os.environ["ENVIRONMENT"] = env
    from app.config.setting import settings

    # 启动uvicorn服务
    uvicorn.run(app="main:create_app", **settings.UVICORN_CONFIG)


@shell_app.command()
def revision(
    message: str,
    env: EnvironmentEnum = typer.Option(
        EnvironmentEnum.DEV, "--env", help="运行环境 (dev, test, prod)"
    ),
):
    """
    生成新的 Al
    embic 迁移脚本。
    """
    os.environ["ENVIRONMENT"] = env.value
    command.revision(alembic_cfg, message=message, autogenerate=True)
    typer.echo(f"迁移脚本已生成: {message}")


@shell_app.command()
def upgrade(
    env: EnvironmentEnum = typer.Option(
        EnvironmentEnum.DEV, "--env", help="运行环境 (dev, test, prod)"
    ),
):
    """
    应用最新的 Alembic 迁移。
    """
    os.environ["ENVIRONMENT"] = env.value
    command.upgrade(alembic_cfg, "head")
    typer.echo("所有迁移已应用。")


if __name__ == "__main__":
    # 启动服务
    # python main.py run    # 启动服务
    # python3 main.py run --env=dev(不加默认为dev)
    # 修改了模型后需要：重新生成迁移文件，然后应用迁移
    # 生成迁移
    # python main.py revision "初始化迁移" --env=dev(不加默认为dev)
    # 应用迁移
    # python main.py upgrade --env=dev(不加默认为dev)

    shell_app()
