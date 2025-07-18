from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any

from src.tasker_client_mac.core import TaskerClient
from src.tasker_client_mac.log import LoggerClient # 假设客户端有自己的日志模块

# 初始化日志
logger = LoggerClient().logger

# Pydantic 模型用于请求体验证
class BuildFlexibleConfigRequest(BaseModel):
    task: str
    type: str
    action: bool

class TaskRequest(BaseModel):
    task: str

class MessageResponse(BaseModel):
    message: str

# FastAPI 应用实例
app = FastAPI()
tasker_client = TaskerClient()
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用生命周期管理。
    在应用启动时初始化调度器和加载任务，在应用关闭时关闭调度器。
    """
    logger.info("客户端 FastAPI 应用启动中...")

    # 配置日志级别
    env = os.environ.get("CLIENT_ENV", "dev")
    log_level = os.environ.get("CLIENT_LOG_LEVEL", "INFO").upper()
    LoggerClient().reset_level(log_level, env)
    logger.info(f"客户端日志级别设置为: {log_level}, 环境: {env}")

    # 添加定时任务
    # 每日早上8点同步看板任务
    scheduler.add_job(tasker_client.kanban, CronTrigger(hour=8, minute=0), name="daily_kanban_sync")

    scheduler.start()
    logger.info("客户端 APScheduler 启动成功。")
    yield
    scheduler.shutdown()
    logger.info("客户端 FastAPI 应用关闭。")

app.router.lifespan_context = lifespan

@app.get("/build_kanban", response_model=MessageResponse)
async def build_kanban():
    """
    自动同步 Obsidian 看板任务，并更新到服务端。
    """
    response = tasker_client.kanban()
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.get("/add_kanban", response_model=MessageResponse)
async def add_kanban():
    """
    手动同步 Obsidian 看板任务（带优先级），并更新到服务端。
    """
    response = tasker_client.add_kanban()
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.post("/build_flexible", response_model=MessageResponse)
async def build_flexible(build_flexible_config: BuildFlexibleConfigRequest):
    """
    灵活添加指定任务或从特定池任务，并更新到服务端。
    """
    response = tasker_client.build_flexible(
        build_flexible_config.task,
        build_flexible_config.type,
        build_flexible_config.action
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.post("/tips", response_model=MessageResponse)
async def tips(task_request: TaskRequest):
    """
    在本地 Obsidian Canvas 文件中添加带分类和颜色的提示/备注。
    """
    response = tasker_client.tips(task_request.task)
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.get("/receive", response_model=MessageResponse)
async def receive():
    """
    从服务端获取当前任务信息并返回。
    """
    response = tasker_client.query_the_current_task()
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.get("/start", response_model=MessageResponse)
async def start():
    """
    启动当前待办任务，如果是 A! 任务则触发本地自动化流程。
    """
    response = tasker_client.start()
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.get("/close", response_model=MessageResponse)
async def close():
    """
    关闭当前进行中任务，触发本地清理并同步到服务端。
    """
    response = tasker_client.close()
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.get("/run", response_model=MessageResponse)
async def run():
    """
    推进当前任务状态，对于 A! 任务会触发本地自动化，并同步状态。
    """
    response = tasker_client.run()
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)