#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import signal
import sys

from apps.worker.runtime.main import main, signal_handler


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n执行机已退出")
    except Exception as exc:
        print(f"\n执行机异常: {exc}")
        sys.exit(1)
