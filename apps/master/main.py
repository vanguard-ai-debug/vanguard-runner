# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.master.api.routes import health_router, task_router, workflow_router
from apps.master.infrastructure.kafka.kafka_producer import get_kafka_producer
from packages.shared.logging.log_component import LOGGER


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _ensure_database_ready(db_health: dict) -> None:
    primary_status = db_health.get("primary")
    replica_status = db_health.get("replica")

    if primary_status != "ok":
        raise RuntimeError(f"主库不可用: {primary_status}")

    if replica_status != "ok":
        LOGGER.logger.warning(f"从库不可用，将依赖读主回退: {replica_status}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGGER.logger.info("应用启动中...")
    LOGGER.logger.info(
        "⚠️ 请确保 Kafka Topics 已手动创建（含 workflow）: "
        "task-workflow-urgent, task-workflow-high, task-workflow-normal"
    )

    try:
        await get_kafka_producer()
        LOGGER.logger.info("✅ Kafka Producer已启动")
    except Exception as exc:
        LOGGER.logger.error(f"❌ Kafka Producer启动失败: {exc}")
        raise RuntimeError("Kafka Producer启动失败") from exc

    from apps.master.infrastructure.db.database_async import check_db_health

    db_health = await check_db_health()
    _ensure_database_ready(db_health)
    LOGGER.logger.info(f"数据库健康状态: {db_health}")
    LOGGER.logger.info("应用启动完成")

    yield

    LOGGER.logger.info("应用关闭中...")

    from apps.master.infrastructure.kafka.kafka_producer import close_kafka_producer
    from apps.master.infrastructure.db.database_async import close_engines

    try:
        await close_kafka_producer()
        LOGGER.logger.info("✅ Kafka Producer已关闭")
    except Exception as exc:
        LOGGER.logger.error(f"❌ Kafka Producer关闭失败: {exc}")

    await close_engines()
    LOGGER.logger.info("数据库连接已关闭")
    LOGGER.logger.info("应用已关闭")


app = FastAPI(lifespan=lifespan)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router.app)
app.include_router(task_router.app)
app.include_router(workflow_router.app)


def main():
    host = os.getenv("MASTER_HOST", "0.0.0.0")
    port = int(os.getenv("MASTER_PORT", "8100"))
    uvicorn.run("apps.master.main:app", host=host, port=port, workers=1, reload=False)


if __name__ == "__main__":
    main()
