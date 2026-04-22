# -*- coding: utf-8 -*-
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from apps.master import main as master_main


def test_ensure_database_ready_accepts_primary_ok_and_replica_warning():
    master_main._ensure_database_ready({"primary": "ok", "replica": "error: down"})


def test_ensure_database_ready_rejects_primary_failure():
    with pytest.raises(RuntimeError, match="主库不可用"):
        master_main._ensure_database_ready({"primary": "error: down", "replica": "ok"})


def test_lifespan_raises_when_kafka_unavailable():
    async def _run():
        with patch.object(master_main, "get_kafka_producer", new=AsyncMock(side_effect=RuntimeError("kafka down"))):
            with pytest.raises(RuntimeError, match="Kafka Producer启动失败"):
                async with master_main.lifespan(master_main.app):
                    pass

    asyncio.run(_run())


def test_lifespan_raises_when_primary_db_unavailable():
    async def _run():
        with patch.object(master_main, "get_kafka_producer", new=AsyncMock(return_value=object())):
            with patch("apps.master.infrastructure.db.database_async.check_db_health", new=AsyncMock(return_value={"primary": "error: down", "replica": "ok"})):
                with pytest.raises(RuntimeError, match="主库不可用"):
                    async with master_main.lifespan(master_main.app):
                        pass

    asyncio.run(_run())


def test_lifespan_success_closes_resources():
    async def _run():
        with patch.object(master_main, "get_kafka_producer", new=AsyncMock(return_value=object())):
            with patch("apps.master.infrastructure.db.database_async.check_db_health", new=AsyncMock(return_value={"primary": "ok", "replica": "ok"})):
                with patch("apps.master.infrastructure.kafka.kafka_producer.close_kafka_producer", new=AsyncMock()) as close_kafka:
                    with patch("apps.master.infrastructure.db.database_async.close_engines", new=AsyncMock()) as close_engines:
                        async with master_main.lifespan(master_main.app):
                            pass

        close_kafka.assert_awaited_once()
        close_engines.assert_awaited_once()

    asyncio.run(_run())


def test_main_uses_configurable_host_and_port():
    with patch.object(master_main.uvicorn, "run") as uvicorn_run:
        with patch.dict("os.environ", {"MASTER_HOST": "127.0.0.1", "MASTER_PORT": "18100"}, clear=False):
            master_main.main()

    uvicorn_run.assert_called_once_with(
        "apps.master.main:app",
        host="127.0.0.1",
        port=18100,
        workers=1,
        reload=False,
    )
