# Python 异步编程指南

本文介绍 Python 中的 async/await 语法，
以及如何使用 asyncio 库进行并发编程。

## 基础概念

asyncio 是 Python 3.4 引入的标准库，用于编写并发代码。

## 使用示例

```python
import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

asyncio.run(main())
```
