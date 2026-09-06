import os
import random
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import aiofiles
from fastapi import UploadFile

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import logger

DANGEROUS_EXTENSIONS = {
    ".py",
    ".pyc",
    ".pyo",
    ".php",
    ".php3",
    ".php4",
    ".php5",
    ".phtml",
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".ps2",
    ".psm1",
    ".psd1",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".wsf",
    ".wsh",
    ".msi",
    ".dll",
    ".so",
    ".dylib",
    ".jar",
    ".class",
    ".jsp",
    ".jspx",
    ".asp",
    ".aspx",
    ".asa",
    ".asax",
    ".cer",
    ".cdx",
    ".config",
    ".htaccess",
    ".htpasswd",
    ".sql",
    ".db",
    ".sqlite",
    ".sqlite3",
}

MIME_TYPE_MAPPING = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    "image/bmp": ".bmp",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/csv": ".csv",
}


class UploadUtil:
    """上传工具类
    """

    @staticmethod
    def generate_random_number() -> str:
        """生成3位随机数字字符串。

        返回:
        - str: 三位随机数字字符串。
        """
        return f"{random.randint(1, 999):03}"

    @staticmethod
    def check_file_exists(filepath: str) -> bool:
        """检查文件是否存在。

        参数:
        - filepath (str): 文件路径。

        返回:
        - bool: 文件是否存在。
        """
        return Path(filepath).exists()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名，移除危险字符和路径穿越。

        参数:
        - filename (str): 原始文件名。

        返回:
        - str: 安全的文件名。
        """
        if not filename:
            return ""
        filename = os.path.basename(filename)
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", filename)
        filename = re.sub(r"\.{2,}", ".", filename)
        filename = filename.strip(". ")
        if not filename:
            filename = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return filename

    @staticmethod
    def check_path_traversal(filename: str) -> bool:
        """检查文件名是否包含路径穿越。

        参数:
        - filename (str): 文件名。

        返回:
        - bool: 是否安全（True 表示安全，False 表示存在路径穿越）。
        """
        dangerous_patterns = ["../", "..\\", "/", "\\", "\0"]
        for pattern in dangerous_patterns:
            if pattern in filename:
                return False
        return True

    @staticmethod
    def get_extension_from_filename(filename: str) -> str:
        """从文件名获取扩展名。

        参数:
        - filename (str): 文件名。

        返回:
        - str: 扩展名（小写，包含点），如 ".jpg"。
        """
        if not filename or "." not in filename:
            return ""
        ext = filename.rsplit(".", 1)[-1].lower()
        return f".{ext}" if ext else ""

    @staticmethod
    def is_dangerous_extension(extension: str) -> bool:
        """检查扩展名是否为危险类型。

        参数:
        - extension (str): 文件扩展名。

        返回:
        - bool: 是否为危险扩展名。
        """
        return extension.lower() in DANGEROUS_EXTENSIONS

    @staticmethod
    def detect_file_type(content: bytes) -> str | None:
        """通过文件内容检测真实文件类型。

        参数:
        - content (bytes): 文件内容（前几字节即可）。

        返回:
        - str | None: 检测到的 MIME 类型，无法识别返回 None。
        """
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
            return "image/gif"
        if content.startswith(b"PK\x03\x04"):
            if b"[Content_Types].xml" in content[:1000]:
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return "application/zip"
        if content.startswith(b"%PDF"):
            return "application/pdf"
        if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            return "application/msword"
        return None

    @classmethod
    def validate_file_extension(cls, extension: str) -> bool:
        """验证文件扩展名是否在允许列表中。

        参数:
        - extension (str): 文件扩展名。

        返回:
        - bool: 是否允许。

        异常:
        - CustomException: 扩展名不允许时抛出。
        """
        ext_lower = extension.lower()
        if cls.is_dangerous_extension(ext_lower):
            raise CustomException(msg=f"不允许上传此类型的文件: {extension}")
        if ext_lower not in settings.ALLOWED_EXTENSIONS:
            raise CustomException(msg=f"文件类型不支持，允许的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}")
        return True

    @classmethod
    def validate_file_content_type(cls, content: bytes, claimed_extension: str) -> bool:
        """验证文件内容类型与声明的扩展名是否匹配。

        参数:
        - content (bytes): 文件内容。
        - claimed_extension (str): 声明的文件扩展名。

        返回:
        - bool: 是否匹配。

        异常:
        - CustomException: 类型不匹配时抛出。
        """
        detected_type = cls.detect_file_type(content)
        if detected_type:
            expected_ext = MIME_TYPE_MAPPING.get(detected_type, "")
            if expected_ext and expected_ext != claimed_extension.lower():
                logger.warning(f"文件类型不匹配: 声明扩展名={claimed_extension}, 检测类型={detected_type}")
        return True

    @staticmethod
    def check_file_size(file: UploadFile) -> bool:
        """校验文件大小是否合法。

        参数:
        - file (UploadFile): 上传的文件对象。

        返回:
        - bool: 文件大小是否合法。

        异常:
        - CustomException: 文件过大时抛出。
        """
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise CustomException(msg=f"文件大小超过限制，最大允许 {settings.MAX_FILE_SIZE // (1024 * 1024)}MB")
        return True

    @classmethod
    def generate_safe_filename(cls, original_filename: str, extension: str) -> str:
        """生成安全的文件名。

        参数:
        - original_filename (str): 原始文件名。
        - extension (str): 文件扩展名。

        返回:
        - str: 安全的文件名。
        """
        safe_name = cls.sanitize_filename(original_filename)
        if safe_name and "." in safe_name:
            name_part = safe_name.rsplit(".", 1)[0]
        else:
            name_part = safe_name or "file"
        name_part = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fa5]", "", name_part)
        if len(name_part) > 50:
            name_part = name_part[:50]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = cls.generate_random_number()
        return f"{name_part}_{timestamp}{settings.UPLOAD_MACHINE}{random_suffix}{extension}"

    @staticmethod
    def check_file_timestamp(filename: str) -> bool:
        """校验文件时间戳是否合法。

        参数:
        - filename (str): 文件名（包含时间戳片段）。

        返回:
        - bool: 时间戳是否合法。
        """
        try:
            name_parts = filename.rsplit(".", 1)[0].split("_")
            timestamp = name_parts[-1].split(settings.UPLOAD_MACHINE)[0]
            datetime.strptime(timestamp, "%Y%m%d%H%M%S")
            return True
        except (ValueError, IndexError):
            return False

    @staticmethod
    def check_file_machine(filename: str) -> bool:
        """校验文件机器码是否合法。

        参数:
        - filename (str): 文件名。

        返回:
        - bool: 机器码是否合法。
        """
        try:
            name_without_ext = filename.rsplit(".", 1)[0]
            return len(name_without_ext) >= 4 and name_without_ext[-4] == settings.UPLOAD_MACHINE
        except IndexError:
            return False

    @staticmethod
    def check_file_random_code(filename: str) -> bool:
        """校验文件随机码是否合法。

        参数:
        - filename (str): 文件名。

        返回:
        - bool: 随机码是否合法（000–999）。
        """
        try:
            code = filename.rsplit(".", 1)[0][-3:]
            return code.isdigit() and 1 <= int(code) <= 999
        except IndexError:
            return False

    @staticmethod
    def _sanitize_target_path(target_path: str) -> str:
        """清理目标路径，移除危险字符和路径穿越。

        参数:
        - target_path (str): 原始目标路径。

        返回:
        - str: 安全的相对路径。

        异常:
        - CustomException: 当路径包含非法字符时抛出。
        """
        if not target_path:
            return ""

        # 检查路径穿越
        if ".." in target_path or "\x00" in target_path:
            logger.error(f"检测到目标路径穿越攻击: {target_path}")
            raise CustomException(msg="非法的目标路径")

        # 规范化路径：移除多余的斜杠、点号
        parts = target_path.replace("\\", "/").split("/")
        safe_parts = []

        for part in parts:
            # 跳过空字符串和单独的点号
            if not part or part == ".":
                continue
            # 移除危险字符
            part = re.sub(r'[<>:"|?*\x00-\x1f]', "", part)
            if part and part != "..":
                safe_parts.append(part)

        return "/".join(safe_parts)

    @staticmethod
    def delete_file(filepath: Path) -> bool:
        """删除文件。

        参数:
        - filepath (Path): 文件路径。

        返回:
        - bool: 删除是否成功。
        """
        try:
            filepath.unlink(missing_ok=True)
            return True
        except OSError:
            return False

    @classmethod
    async def upload_file(
        cls,
        file: UploadFile,
        base_url: str,
        upload_type: str = "file",
        target_path: str | None = None,
    ) -> tuple[str, Path, str]:
        """安全文件上传。

        参数:
        - file (UploadFile): 上传的文件对象。
        - base_url (str): 基础 URL。
        - upload_type (str): 上传类型，可选值:
          - "file": 通用文件 (默认)
          - "avatar": 头像图片
          - "param": 参数配置
          - "resource": 监控资源
        - target_path (str | None): 目标目录路径（相对路径），仅 resource 类型支持。
          例如: "images", "documents/2024"

        返回:
        - tuple[str, Path, str]: (文件名, 文件路径, 文件 URL)。

        异常:
        - CustomException: 当文件校验失败时抛出。
        """
        if not file or not file.filename:
            raise CustomException(msg="请选择要上传的文件")

        original_filename = file.filename

        if not cls.check_path_traversal(original_filename):
            raise CustomException(msg="文件名包含非法字符", data=original_filename)

        extension = cls.get_extension_from_filename(original_filename)
        if not extension:
            raise CustomException(msg="无法识别文件类型")

        cls.validate_file_extension(extension)

        cls.check_file_size(file)

        content = await file.read()
        await file.seek(0)

        cls.validate_file_content_type(content, extension)

        safe_filename = cls.generate_safe_filename(original_filename, extension)

        try:
            # 根据上传类型选择保存目录
            type_subdir = {
                "avatar": "avatar",
                "param": "param",
                "resource": "resource",
            }.get(upload_type, "file")

            # 构建目录路径
            if target_path and upload_type == "resource":
                # target_path 是相对于 upload/resource 的子目录
                # 清理路径，防止路径穿越
                # 资源管理模块：文件直接保存在目标目录，不自动创建日期子目录
                safe_target = cls._sanitize_target_path(target_path)
                dir_path = settings.UPLOAD_FILE_PATH.joinpath(type_subdir, safe_target)
            elif upload_type == "resource":
                # 资源管理模块根目录上传：直接保存在 upload/resource/ 下
                dir_path = settings.UPLOAD_FILE_PATH.joinpath(type_subdir)
            else:
                # 其他类型：按日期子目录组织
                dir_path = settings.UPLOAD_FILE_PATH.joinpath(type_subdir, datetime.now().strftime("%Y/%m/%d"))

            dir_path.mkdir(parents=True, exist_ok=True)

            filepath = dir_path.joinpath(safe_filename)

            if not filepath.resolve().is_relative_to(settings.UPLOAD_FILE_PATH.resolve()):
                logger.error(f"检测到路径穿越攻击，目标路径: {filepath}")
                raise CustomException(msg="非法的文件路径")

            file_url = urljoin(base_url, str(filepath))

            chunk_size = 8 * 1024 * 1024
            async with aiofiles.open(filepath, "wb") as f:
                while chunk := await file.read(chunk_size):
                    await f.write(chunk)

            return safe_filename, filepath, file_url

        except CustomException:
            raise
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise CustomException(msg=f"文件上传失败: {e}")

    @staticmethod
    def get_file_tree(file_path: str) -> list[dict]:
        """获取文件树结构。

        参数:
        - file_path (str): 文件路径。

        返回:
        - list[dict]: 文件树列表。
        """
        return [{"name": item.name, "is_dir": item.is_dir()} for item in Path(file_path).iterdir()]
