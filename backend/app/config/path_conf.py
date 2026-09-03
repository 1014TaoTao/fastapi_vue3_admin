from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.parent

# alembic 迁移文件存放路径
ALEMBIC_VERSION_DIR = BASE_DIR / "app" / "alembic" / "versions"

# 日志文件路径
LOG_DIR = BASE_DIR / "logs"

# 静态资源目录
STATIC_DIR = BASE_DIR / "static"

# 环境配置目录
ENV_DIR = BASE_DIR / "env"

# 初始化脚本
SCRIPT_DIR: Path = BASE_DIR / "sql"

# 模版文件配置（统一管理代码生成模板 + HTML 模板）
TEMPLATE_DIR: Path = BASE_DIR / "templates"

# 前端构建输出目录
FRONTEND_DIST_DIR: Path = BASE_DIR / "dist"

# banner.txt 文件路径
BANNER_FILE = BASE_DIR / "banner.txt"
