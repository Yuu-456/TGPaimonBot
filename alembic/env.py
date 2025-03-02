from itertools import chain
import os
import asyncio
from importlib import import_module
from logging.config import fileConfig
from typing import Iterator

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from sqlmodel import SQLModel

from alembic import context

from utils.const import CORE_DIR, PLUGIN_DIR, PROJECT_ROOT
from utils.log import logger

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def scan_models() -> Iterator[str]:
    """扫描 core 和 plugins 目录下所有 models.py 模块。
    我们规定所有插件的 model 都需要放在名为 models.py 的文件里。"""
    dirs = [CORE_DIR, PLUGIN_DIR]

    for path in chain(*[d.glob("**/models.py") for d in dirs]):
        yield str(path.relative_to(PROJECT_ROOT).with_suffix("")).replace(os.sep, ".")


def import_models():
    """导入我们所有的 models，使 alembic 可以自动对比 db scheme 创建 migration revision"""
    for pkg in scan_models():
        try:
            import_module(pkg)  # 导入 models
        except Exception as e:  # pylint: disable=W0703
            logger.error(f'在导入文件 "{pkg}" 的过程中遇到了错误: \n[red bold]{type(e).__name__}: {e}[/]')


# register our models for alembic to auto-generate migrations
import_models()

target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# here we allow ourselves to pass interpolation vars to alembic.ini
# from the application config module
from core.config import config as botConfig

section = config.config_ini_section
config.set_section_option(section, "DB_HOST", botConfig.mysql.host)
config.set_section_option(section, "DB_PORT", str(botConfig.mysql.port))
config.set_section_option(section, "DB_USERNAME", botConfig.mysql.username)
config.set_section_option(section, "DB_PASSWORD", botConfig.mysql.password)
config.set_section_option(section, "DB_DATABASE", botConfig.mysql.database)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
