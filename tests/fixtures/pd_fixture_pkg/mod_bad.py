# -*- coding: utf-8 -*-
"""import 时失败，用于验证发现逻辑吞掉单模块错误且不中断其它模块。"""
raise RuntimeError("intentional import failure for tests")
