# -*- coding:utf-8 -*-

from datetime import datetime, time
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlglot.expressions import Expression
from typing import List

from .model import GenTableModel, GenTableColumnModel
from app.config.setting import settings
from app.common.request import PaginationService
from .schema import (
    GenTableBaseSchema,
    GenTableColumnBaseSchema,
    GenTableColumnSchema,
    GenTableSchema,
)
from .param import GenTableQueryParam, GenTableColumnBaseSchema


class GenTableDao:
    """
    代码生成业务表模块数据库操作层
    """

    @classmethod
    async def get_gen_table_by_id(cls, db: AsyncSession, table_id: int):
        """
        根据业务表id获取需要生成的业务表信息

        :param db: orm对象
        :param table_id: 业务表id
        :return: 需要生成的业务表信息对象
        """
        gen_table_info = (
            (
                await db.execute(
                    select(GenTableModel).options(selectinload(GenTableModel.columns)).where(GenTableModel.table_id == table_id)
                )
            )
            .scalars()
            .first()
        )

        return gen_table_info

    @classmethod
    async def get_gen_table_by_name(cls, db: AsyncSession, table_name: str):
        """
        根据业务表名称获取需要生成的业务表信息

        :param db: orm对象
        :param table_name: 业务表名称
        :return: 需要生成的业务表信息对象
        """
        gen_table_info = (
            (
                await db.execute(
                    select(GenTableModel).options(selectinload(GenTableModel.columns)).where(GenTableModel.table_name == table_name)
                )
            )
            .scalars()
            .first()
        )

        return gen_table_info

    @classmethod
    async def get_gen_table_all(cls, db: AsyncSession):
        """
        获取所有业务表信息

        :param db: orm对象
        :return: 所有业务表信息
        """
        gen_table_all = (await db.execute(select(GenTableModel).options(selectinload(GenTableModel.columns)))).scalars().all()

        return gen_table_all

    @classmethod
    async def create_table_by_sql_dao(cls, db: AsyncSession, sql_statements: List[Expression]):
        """
        根据sql语句创建表结构

        :param db: orm对象
        :param sql_statements: sql语句的ast列表
        :return:
        """
        for sql_statement in sql_statements:
            sql = sql_statement.sql(dialect=settings.DATABASE_TYPE)
            await db.execute(text(sql))

    @classmethod
    async def get_gen_table_list(cls, db: AsyncSession, query_object: GenTableQueryParam, is_page: bool = False):
        """
        根据查询参数获取代码生成业务表列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 代码生成业务表列表信息对象
        """
        query = (
            select(GenTableModel)
            .options(selectinload(GenTableModel.columns))
            .where(
                func.lower(GenTableModel.table_name).like(f'%{query_object.table_name.lower()}%')
                if query_object.table_name
                else True,
                func.lower(GenTableModel.table_comment).like(f'%{query_object.table_comment.lower()}%')
                if query_object.table_comment
                else True,
                GenTableModel.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .distinct()
        )
        gen_table_list = await PaginationService.paginate(db, query, query_object.page_no, query_object.page_size, is_page)

        return gen_table_list

    @classmethod
    async def get_gen_db_table_list(cls, db: AsyncSession, query_object: GenTableQueryParam, is_page: bool = False):
        """
        根据查询参数获取数据库列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 数据库列表信息对象
        """
        if settings.DATABASE_TYPE == 'postgresql':
            query_sql = """
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time
            from 
                list_table
            where 
                table_name not like 'apscheduler_%' 
                and table_name not like 'gen_%'
                and table_name not in (select table_name from gen_table)
            """
        else:
            query_sql = """
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time
            from 
                information_schema.tables
            where 
                table_schema = (select database())
                and table_name not like 'apscheduler\_%' 
                and table_name not like 'gen\_%'
                and table_name not in (select table_name from gen_table)
            """
        if query_object.table_name:
            query_sql += """and lower(table_name) like lower(concat('%', :table_name, '%'))"""
        if query_object.table_comment:
            query_sql += """and lower(table_comment) like lower(concat('%', :table_comment, '%'))"""
        if query_object.begin_time:
            if settings.DATABASE_TYPE == 'postgresql':
                query_sql += """and create_time::date >= to_date(:begin_time, 'yyyy-MM-dd')"""
            else:
                query_sql += """and date_format(create_time, '%Y%m%d') >= date_format(:begin_time, '%Y%m%d')"""
        if query_object.end_time:
            if settings.DATABASE_TYPE == 'postgresql':
                query_sql += """and create_time::date <= to_date(:end_time, 'yyyy-MM-dd')"""
            else:
                query_sql += """and date_format(create_time, '%Y%m%d') >= date_format(:end_time, '%Y%m%d')"""
        query_sql += """order by create_time desc"""
        query = select(
            text(query_sql).bindparams(
                **{
                    k: v
                    for k, v in query_object.model_dump(exclude_none=True, exclude={'page_num', 'page_size'}).items()
                }
            )
        )
        gen_db_table_list = await PaginationService.paginate(db, query, query_object.page_no, query_object.page_size, is_page)

        return gen_db_table_list

    @classmethod
    async def get_gen_db_table_list_by_names(cls, db: AsyncSession, table_names: List[str]):
        """
        根据业务表名称组获取数据库列表信息

        :param db: orm对象
        :param table_names: 业务表名称组
        :return: 数据库列表信息对象
        """
        if settings.DATABASE_TYPE == 'postgresql':
            query_sql = """
            select
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time 
            from 
                list_table
            where 
                table_name not like 'qrtz_%' 
                and table_name not like 'gen_%' 
                and table_name = any(:table_names)
            """
        else:
            query_sql = """
            select
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time 
            from 
                information_schema.tables
            where 
                table_name not like 'qrtz\_%' 
                and table_name not like 'gen\_%' 
                and table_schema = (select database())
                and table_name in :table_names
            """
        query = text(query_sql).bindparams(table_names=tuple(table_names))
        gen_db_table_list = (await db.execute(query)).fetchall()

        return gen_db_table_list

    @classmethod
    async def add_gen_table_dao(cls, db: AsyncSession, gen_table: GenTableModel):
        """
        新增业务表数据库操作

        :param db: orm对象
        :param gen_table: 业务表对象
        :return:
        """
        db_gen_table = GenTableModel(**GenTableBaseSchema(**gen_table.model_dump(by_alias=True)).model_dump())
        db.add(db_gen_table)
        await db.flush()

        return db_gen_table

    @classmethod
    async def edit_gen_table_dao(cls, db: AsyncSession, gen_table: dict):
        """
        编辑业务表数据库操作

        :param db: orm对象
        :param gen_table: 需要更新的业务表字典
        :return:
        """
        await db.execute(update(GenTableModel), [GenTableBaseSchema(**gen_table).model_dump()])

    @classmethod
    async def delete_gen_table_dao(cls, db: AsyncSession, gen_table: GenTableModel):
        """
        删除业务表数据库操作

        :param db: orm对象
        :param gen_table: 业务表对象
        :return:
        """
        await db.execute(delete(GenTableModel).where(GenTableModel.table_id.in_([gen_table.table_id])))


class GenTableColumnDao:
    """
    代码生成业务表字段模块数据库操作层
    """

    @classmethod
    async def get_gen_table_column_list_by_table_id(cls, db: AsyncSession, table_id: int):
        """
        根据业务表id获取需要生成的业务表字段列表信息

        :param db: orm对象
        :param table_id: 业务表id
        :return: 需要生成的业务表字段列表信息对象
        """
        gen_table_column_list = (
            (
                await db.execute(
                    select(GenTableColumnModel).where(GenTableColumnModel.table_id == table_id).order_by(GenTableColumnModel.sort)
                )
            )
            .scalars()
            .all()
        )

        return gen_table_column_list

    @classmethod
    async def get_gen_db_table_columns_by_name(cls, db: AsyncSession, table_name: str):
        """
        根据业务表名称获取业务表字段列表信息

        :param db: orm对象
        :param table_name: 业务表名称
        :return: 业务表字段列表信息对象
        """
        if settings.DATABASE_TYPE == 'postgresql':
            query_sql = """
            select
                column_name, is_required, is_pk, sort, column_comment, is_increment, column_type
            from
                list_column
            where
                table_name = :table_name
            """
        else:
            query_sql = """
            select 
                column_name as column_name,
                case 
                    when is_nullable = 'no' and column_key != 'PRI' then '1' 
                    else '0' 
                end as is_required,
                case 
                    when column_key = 'PRI' then '1' 
                    else '0' 
                end as is_pk,
                ordinal_position as sort,
                column_comment as column_comment,
                case 
                    when extra = 'auto_increment' then '1' 
                    else '0' 
                end as is_increment,
                column_type as column_type
            from 
                information_schema.columns
            where 
                table_schema = (select database()) 
                and table_name = :table_name
            order by 
                ordinal_position
            """
        query = text(query_sql).bindparams(table_name=table_name)
        gen_db_table_columns = (await db.execute(query)).fetchall()

        return gen_db_table_columns

    @classmethod
    async def add_gen_table_column_dao(cls, db: AsyncSession, gen_table_column: GenTableColumnModel):
        """
        新增业务表字段数据库操作

        :param db: orm对象
        :param gen_table_column: 岗位对象
        :return:
        """
        db_gen_table_column = GenTableColumnModel(
            **GenTableColumnBaseSchema(**gen_table_column.model_dump(by_alias=True)).model_dump()
        )
        db.add(db_gen_table_column)
        await db.flush()

        return db_gen_table_column

    @classmethod
    async def edit_gen_table_column_dao(cls, db: AsyncSession, gen_table_column: dict):
        """
        编辑业务表字段数据库操作

        :param db: orm对象
        :param gen_table_column: 需要更新的业务表字段字典
        :return:
        """
        await db.execute(update(GenTableColumnModel), [GenTableColumnBaseSchema(**gen_table_column).model_dump()])

    @classmethod
    async def delete_gen_table_column_by_table_id_dao(cls, db: AsyncSession, gen_table_column: GenTableColumnModel):
        """
        通过业务表id删除业务表字段数据库操作

        :param db: orm对象
        :param gen_table_column: 业务表字段对象
        :return:
        """
        await db.execute(delete(GenTableColumnModel).where(GenTableColumnModel.table_id.in_([gen_table_column.table_id])))

    @classmethod
    async def delete_gen_table_column_by_column_id_dao(cls, db: AsyncSession, gen_table_column: GenTableColumnModel):
        """
        通过业务字段id删除业务表字段数据库操作

        :param db: orm对象
        :param post: 业务表字段对象
        :return:
        """
        await db.execute(delete(GenTableColumnModel).where(GenTableColumnModel.column_id.in_([gen_table_column.column_id])))
