from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any

from src.taskerz.workday_facade import WorkdayFacade
from src.taskerz.log import Logger

# 初始化日志
logger = Logger().logger

# Pydantic 模型用于请求体验证
class TaskListRequest(BaseModel):
    tasks: List[str]

class TaskListJSONRequest(BaseModel):
    tasks: List[Dict[str, str]]

class MessageResponse(BaseModel):
    message: str

# FastAPI 应用实例
app = FastAPI()
workday_facade = WorkdayFacade()
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用生命周期管理。
    在应用启动时初始化调度器和加载任务，在应用关闭时关闭调度器。
    """
    logger.info("FastAPI 应用启动中...")

    # 配置日志级别
    env = os.environ.get("ENV", "dev")
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    Logger().reset_level(log_level, env)
    logger.info(f"日志级别设置为: {log_level}, 环境: {env}")

    # 清空所有任务
    workday_facade.clear()
    workday_facade.clear_new()

    # 添加定时任务
    # 每日午夜清空所有任务
    scheduler.add_job(workday_facade.clear, CronTrigger(hour=0, minute=0), name="daily_midnight_clear")
    scheduler.add_job(workday_facade.clear_new, CronTrigger(hour=0, minute=0), name="daily_midnight_clear_new")

    # 工作日早上8:50加载清晨任务
    scheduler.add_job(workday_facade._morning_tasks, CronTrigger(day_of_week='mon-fri', hour=8, minute=50), name="weekday_morning_tasks")
    # 示例：为特定用户加载清晨任务
    scheduler.add_job(workday_facade._morning_tasks_new, CronTrigger(day_of_week='mon-fri', hour=8, minute=50), args=["user_a"], name="weekday_morning_tasks_user_a")

    scheduler.start()
    logger.info("APScheduler 启动成功。")
    yield
    scheduler.shutdown()
    logger.info("FastAPI 应用关闭。")

app.router.lifespan_context = lifespan

@app.get("/receive", response_model=MessageResponse)
async def receive():
    """
    获取当前（第一个未完成）任务的信息和提示。
    """
    task_info = workday_facade.get_current_task_info()
    if "message" in task_info:
        return JSONResponse(content={"message": task_info["message"]}, status_code=status.HTTP_200_OK)
    return JSONResponse(content={"message": f"当前任务：{task_info['name']} ({task_info['status']})\n提示: {task_info['prompt']}"}, status_code=status.HTTP_200_OK)

@app.get("/receive_new/{id}", response_model=MessageResponse)
async def receive_new(id: str):
    """
    获取指定用户（由 `id` 标识）的当前任务信息和提示。
    """
    task_info = workday_facade.get_current_task_info_new(id)
    if "message" in task_info:
        return JSONResponse(content={"message": task_info["message"]}, status_code=status.HTTP_200_OK)
    return JSONResponse(content={"message": f"当前任务：{task_info['name']} ({task_info['status']})\n提示: {task_info['prompt']}"}, status_code=status.HTTP_200_OK)

@app.get("/complete", response_model=MessageResponse)
async def complete():
    """
    推进当前任务状态，并返回下一个任务信息。
    """
    response = workday_facade.complete_current_task()
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.get("/complete_new/{id}", response_model=MessageResponse)
async def complete_new(id: str):
    """
    推进指定用户当前任务状态，并返回下一个任务信息。
    """
    response = workday_facade.complete_current_task_new(id)
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)

@app.post("/update_tasks", response_model=MessageResponse)
async def update_tasks(task_request: TaskListRequest):
    """
    批量添加任务，旧版接口。
    """
    workday_facade.add_person_tasks(task_request.tasks)
    return JSONResponse(content={"message": "人工任务示例已添加"}, status_code=status.HTTP_200_OK)

@app.post("/update_tasks_new", response_model=MessageResponse)
async def update_tasks_new(task_request: TaskListJSONRequest):
    """
    批量添加任务，支持指定 `belong` 字段。
    """
    workday_facade.add_person_tasks_new(task_request.tasks)
    return JSONResponse(content={"message": "人工任务示例已添加"}, status_code=status.HTTP_200_OK)

@app.get("/list_tasks", response_model=MessageResponse)
async def list_tasks():
    """
    列出所有老版任务及其状态。
    """
    tasks_status = workday_facade.get_all_tasks_status()
    message = "---\n所有任务状态 ---\n"
    if not tasks_status:
        message += "无任务。"
    else:
        for task in tasks_status:
            message += f"- {task['name']}: 任务 '{task['name']}' 的状态是：{task['status']}\n"
    return JSONResponse(content={"message": message}, status_code=status.HTTP_200_OK)

@app.get("/list_tasks_new/{id}", response_model=MessageResponse)
async def list_tasks_new(id: str):
    """
    列出指定用户所有任务及其状态。
    """
    tasks_status = workday_facade.get_all_tasks_status_new(id)
    message = f"---\n用户 '{id}' 的所有任务状态 ---\n"
    if not tasks_status:
        message += "无任务。"
    else:
        for task in tasks_status:
            message += f"- {task['name']}: 任务 '{task['name']}' 的状态是：{task['status']}\n"
    return JSONResponse(content={"message": message}, status_code=status.HTTP_200_OK)

@app.get("/morning", response_model=MessageResponse)
async def morning():
    """
    手动触发加载预设清晨任务（老版）。
    """
    workday_facade._morning_tasks()
    return JSONResponse(content={"message": "清晨任务已加载。"}, status_code=status.HTTP_200_OK)

@app.get("/morning_new/{id}", response_model=MessageResponse)
async def morning_new(id: str):
    """
    手动触发加载指定用户预设清晨任务（新版）。
    """
    workday_facade._morning_tasks_new(id)
    return JSONResponse(content={"message": f"用户 '{id}' 的清晨任务已加载。"}, status_code=status.HTTP_200_OK)

@app.get("/clear", response_model=MessageResponse)
async def clear():
    """
    清空所有老版任务。
    """
    workday_facade.clear()
    return JSONResponse(content={"message": "所有老版任务已清空。"}, status_code=status.HTTP_200_OK)

@app.get("/clear_new/{id}", response_model=MessageResponse)
async def clear_new(id: str):
    """
    清空指定用户所有任务。
    """
    workday_facade.clear_new(id)
    return JSONResponse(content={"message": f"用户 '{id}' 的所有任务已清空。"}, status_code=status.HTTP_200_OK)

if __name__ == "__main__":
    # 运行 FastAPI 应用
    # 使用 --reload 可以在代码修改时自动重启
    # host="0.0.0.0" 允许从外部访问
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
