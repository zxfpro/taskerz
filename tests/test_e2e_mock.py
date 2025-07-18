import pytest
from httpx import AsyncClient
import uvicorn
import threading
import time
from src.taskerz.server import app as server_app
from src.tasker_client_mac.server import app as client_app
from src.taskerz.task_manager import TaskManager
from unittest.mock import patch, MagicMock
from src.tasker_client_mac.core import TaskerClient

# 定义 FastAPI 应用的端口
SERVER_PORT = 8000
CLIENT_PORT = 8001

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

def run_server():
    """在单独的线程中运行 FastAPI 服务端"""
    uvicorn.run(server_app, host="127.0.0.1", port=SERVER_PORT, log_level="info")

def run_client():
    """在单独的线程中运行 FastAPI 客户端"""
    uvicorn.run(client_app, host="127.0.0.1", port=CLIENT_PORT, log_level="info")

@pytest.fixture(scope="module", autouse=True)
async def setup_e2e_environment():
    """
    在测试模块开始前启动服务端和客户端，并在测试模块结束后关闭。
    """
    # Mock TaskerClient 的外部依赖
    with patch.object(TaskerClient, 'display', new_callable=MagicMock) as mock_display, \
         patch.object(TaskerClient, 'shortcut', new_callable=MagicMock) as mock_shortcut, \
         patch.object(TaskerClient, 'manager', new_callable=MagicMock) as mock_kanban_manager, \
         patch.object(TaskerClient, 'canvas', new_callable=MagicMock) as mock_canvas:

        # 启动服务端
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print(f"Server started on port {SERVER_PORT}")

        # 启动客户端
        client_thread = threading.Thread(target=run_client, daemon=True)
        client_thread.start()
        print(f"Client started on port {CLIENT_PORT}")

        # 等待服务启动
        time.sleep(5) # 给予足够的时间让服务启动

        # 清空 TaskManager 状态，确保测试环境干净
        TaskManager._instance = None
        TaskManager() # 重新初始化单例

        yield

        # 在测试结束后，由于是 daemon 线程，它们会在主程序退出时自动关闭
        print("E2E environment teardown complete.")

@pytest.fixture(scope="function", autouse=True)
async def clear_tasks_between_tests():
    """
    每个测试用例执行前清空服务端和客户端的任务。
    """
    async with AsyncClient(base_url=f"http://127.0.0.1:{SERVER_PORT}") as server_client:
        await server_client.get("/clear")
        await server_client.get("/clear_new/user_e2e")
    print("Tasks cleared before test.")
    yield

@pytest.mark.asyncio
async def test_e2e_task_flow():
    """
    测试客户端和服务端之间的端到端任务流程。
    1. 客户端添加任务到服务端。
    2. 客户端查询当前任务。
    3. 客户端完成任务。
    4. 客户端再次查询，验证任务状态更新。
    """
    server_base_url = f"http://127.0.0.1:{SERVER_PORT}"
    client_base_url = f"http://127.0.0.1:{CLIENT_PORT}"

    async with AsyncClient(base_url=server_base_url) as server_http_client:
        async with AsyncClient(base_url=client_base_url) as client_http_client:
            # 1. 客户端添加任务到服务端 (通过客户端的 build_flexible 接口)
            print("Step 1: Client adding task to server...")
            add_task_response = await client_http_client.post(
                "/build_flexible",
                json={"task": "E2E Test Task", "type": "flex", "action": True}
            )
            assert add_task_response.status_code == 200
            assert add_task_response.json()["message"] == "successed build"

            # 验证服务端任务列表
            server_list_response = await server_http_client.get("/list_tasks_new/flexible")
            assert server_list_response.status_code == 200
            assert "E2E Test Task" in server_list_response.json()["message"]
            print("Task added and verified on server.")

            # 2. 客户端查询当前任务 (通过客户端的 receive 接口)
            print("Step 2: Client querying current task...")
            receive_response = await client_http_client.get("/receive")
            assert receive_response.status_code == 200
            assert "当前任务：E2E Test Task (待办)" in receive_response.json()["message"]
            print("Current task received by client.")

            # 3. 客户端启动任务 (通过客户端的 start 接口)
            print("Step 3: Client starting task...")
            start_response = await client_http_client.get("/start")
            assert start_response.status_code == 200
            assert "task: E2E Test Task 进行中" in start_response.json()["message"]
            print("Task started by client.")

            # 4. 客户端完成任务 (通过客户端的 close 接口)
            print("Step 4: Client completing task...")
            complete_response = await client_http_client.get("/close")
            assert complete_response.status_code == 200
            assert "任务 'E2E Test Task' 状态更新为：进行中" in complete_response.json()["message"] # 第一次完成是 InProgress
            print("Task completed by client (first step).")

            # 再次完成，使其变为 Completed
            complete_response = await client_http_client.get("/close")
            assert complete_response.status_code == 200
            assert "任务 'E2E Test Task' 状态更新为：完成" in complete_response.json()["message"]
            print("Task completed by client (second step).")

            # 5. 客户端再次查询，验证任务状态更新
            print("Step 5: Client querying task status after completion...")
            final_receive_response = await client_http_client.get("/receive")
            assert final_receive_response.status_code == 200
            assert "所有任务已完成！" in final_receive_response.json()["message"]
            print("Task status verified as completed.")

            # 验证服务端任务列表，确认任务已完成
            final_server_list_response = await server_http_client.get("/list_tasks_new/flexible")
            assert final_server_list_response.status_code == 200
            assert "E2E Test Task" in final_server_list_response.json()["message"]
            assert "完成" in final_server_list_response.json()["message"]
            print("Server task list verified after completion.")