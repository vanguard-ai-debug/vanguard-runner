from __future__ import annotations

from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from packages.shared.logging.log_component import LOGGER
from packages.shared.settings.runtime import get_redis_settings


class RedisClient:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client: Optional[aioredis.Redis] = None

    async def connect(self):
        self.client = await aioredis.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            password=self.password,
            encoding="utf-8",
            decode_responses=True,
        )
        await self.client.ping()
        LOGGER.logger.info(f"Redis连接成功: {self.host}:{self.port}/{self.db}")

    async def close(self):
        if self.client:
            await self.client.close()
            LOGGER.logger.info("Redis连接已关闭")

    async def set_task_status(
        self,
        task_id: str,
        status: str,
        progress: int = 0,
        worker_id: str = "",
        started_at: str = "",
        finished_at: str = "",
        retry_count: int = 0,
        expire: int = 86400,
    ):
        key = f"task:{task_id}"
        await self.client.hset(
            key,
            mapping={
                "status": status,
                "progress": str(progress),
                "worker_id": worker_id,
                "started_at": started_at,
                "finished_at": finished_at,
                "retry_count": str(retry_count),
            },
        )
        await self.client.expire(key, expire)

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, str]]:
        result = await self.client.hgetall(f"task:{task_id}")
        return result or None

    async def update_task_field(self, task_id: str, field: str, value: str):
        await self.client.hset(f"task:{task_id}", field, value)

    async def get_all_workers(self) -> Dict[str, Dict[str, str]]:
        workers: Dict[str, Dict[str, str]] = {}
        async for key in self.client.scan_iter(match="worker:*"):
            worker_id = key.replace("worker:", "")
            worker_info = await self.client.hgetall(key)
            if worker_info:
                workers[worker_id] = worker_info
        return workers


_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    global _redis_client
    if _redis_client is None:
        settings = get_redis_settings()
        _redis_client = RedisClient(**settings)
        await _redis_client.connect()
    return _redis_client


async def close_redis_client():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
