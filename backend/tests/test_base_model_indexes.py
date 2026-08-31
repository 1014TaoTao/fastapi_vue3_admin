"""模型通用软删除索引回归测试。

背景：子类一旦显式声明 ``__table_args__``，会**整体覆盖** ``ModelMixin`` 的
``declared_attr.directive``（SQLAlchemy 不做自动合并），导致
``ix_{表}_status_deleted`` / ``ix_{表}_created_deleted`` 两个索引丢失——
而软删除查询全都带 ``is_deleted`` 条件。

``core/base_model.py`` 的 ``_DeclarativeMeta`` 会在 declarative 扫描之前合并补全这两个索引。
本测试用于验证合并逻辑对所有模型生效，并防止后续新增模型时再次退化。

注意：``status`` 列由各模型自行声明（不在 ``ModelMixin`` 中），因此只有确实存在该列的表
才应带 ``ix_{表}_status_deleted``；``created_time`` / ``is_deleted`` 由 Mixin 提供，每张表都应有。
"""

import importlib
import pkgutil

import pytest

import app.api.v1
from app.core.base_model import MappedBase, ModelMixin


def _import_all_models() -> None:
    """导入 api/v1 下所有 model 模块，使 ORM 映射全部注册。"""
    for mod in pkgutil.walk_packages(app.api.v1.__path__, prefix="app.api.v1."):
        if mod.name.endswith(".model"):
            importlib.import_module(mod.name)


def _iter_model_mixin_tables():
    """产出所有继承 ModelMixin 的具体模型与其主表。"""
    for mapper in MappedBase.registry.mappers:
        cls = mapper.class_
        if issubclass(cls, ModelMixin) and not cls.__dict__.get("__abstract__"):
            yield cls, mapper.local_table


@pytest.fixture(scope="module", autouse=True)
def _load_models():
    """本模块用例执行前先导入全部模型。"""
    _import_all_models()


def test_models_are_imported():
    """导入逻辑本身要有效，否则后面的断言会"空跑通过"。"""
    tables = list(_iter_model_mixin_tables())
    assert tables, "未发现任何 ModelMixin 模型，模型导入逻辑可能失效"


def test_soft_delete_indexes_exist():
    """每张继承 ModelMixin 的表都应具备与其列匹配的软删除索引。"""
    missing: list[str] = []
    for cls, table in _iter_model_mixin_tables():
        if cls.__dict__.get("__table_args_skip_base_index__"):
            continue
        index_names = {idx.name for idx in table.indexes}
        expected = [f"ix_{table.name}_created_deleted"]
        if "status" in table.columns:
            expected.append(f"ix_{table.name}_status_deleted")
        for want in expected:
            if want not in index_names:
                missing.append(f"{cls.__name__}({table.name}) 缺少 {want}")

    assert not missing, "以下模型缺少通用软删除索引:\n" + "\n".join(missing)


def test_no_index_on_missing_column():
    """不得给没有 status 列的表建 status 索引，否则建表时会因列不存在而失败。"""
    invalid: list[str] = []
    for cls, table in _iter_model_mixin_tables():
        index_names = {idx.name for idx in table.indexes}
        want = f"ix_{table.name}_status_deleted"
        if want in index_names and "status" not in table.columns:
            invalid.append(f"{cls.__name__}({table.name}) 无 status 列却建了 {want}")

    assert not invalid, "以下模型索引引用了不存在的列:\n" + "\n".join(invalid)


def test_no_duplicate_index_names():
    """合并逻辑不得与子类自定义索引重名，否则建表时会重复创建。"""
    for cls, table in _iter_model_mixin_tables():
        names = [idx.name for idx in table.indexes]
        duplicated = {name for name in names if names.count(name) > 1}
        assert not duplicated, f"{cls.__name__}({table.name}) 存在重复索引名: {duplicated}"
