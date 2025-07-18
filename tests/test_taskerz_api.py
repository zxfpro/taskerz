import pytest
from httpx import AsyncClient
from taskerz.server import app
from taskerz.task_manager import TaskManager

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="function", autouse=True)
async def clear_task_manager():
    """
    每次测试前清空 TaskManager 实例，确保测试独立性。
    """
    TaskManager._instance = None
    TaskManager() # 重新初始化单例
    yield

@pytest.mark.asyncio
async def test_receive_empty_tasks():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/receive")
        assert response.status_code == 200
        assert response.json() == {"message": "所有任务已完成！"}

@pytest.mark.asyncio
async def test_receive_new_empty_tasks():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/receive_new/user_test")
        assert response.status_code == 200
        assert response.json() == {"message": "所有任务已完成！"}

@pytest.mark.asyncio
async def test_update_tasks_and_receive():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Add tasks
        response = await client.post("/update_tasks", json={"tasks": ["Task A", "Task B"]})
        assert response.status_code == 200
        assert response.json() == {"message": "人工任务示例已添加"}

        # Receive current task
        response = await client.get("/receive")
        assert response.status_code == 200
        assert "当前任务：Task A (待办)" in response.json()["message"]

@pytest.mark.asyncio
async def test_update_tasks_new_and_receive_new():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Add new tasks for user_a
        response = await client.post("/update_tasks_new", json={"tasks": [{"content": "Task A", "belong": "user_a"}, {"content": "Task B", "belong": "user_a"}]})
        assert response.status_code == 200
        assert response.json() == {"message": "人工任务示例已添加"}

        # Receive current task for user_a
        response = await client.get("/receive_new/user_a")
        assert response.status_code == 200
        assert "当前任务：Task A (待办)" in response.json()["message"]

        # Add new tasks for user_b
        response = await client.post("/update_tasks_new", json={"tasks": [{"content": "Task C", "belong": "user_b"}]})
        assert response.status_code == 200

        # Receive current task for user_b
        response = await client.get("/receive_new/user_b")
        assert response.status_code == 200
        assert "当前任务：Task C (待办)" in response.json()["message"]

@pytest.mark.asyncio
async def test_complete_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/update_tasks", json={"tasks": ["Task X", "Task Y"]})

        # Complete Task X (Todo -> InProgress)
        response = await client.get("/complete")
        assert response.status_code == 200
        assert "任务 'Task X' 状态更新为：进行中" in response.json()["message"]
        assert "当前任务：Task X (进行中)" in response.json()["message"]

        # Complete Task X (InProgress -> Completed)
        response = await client.get("/complete")
        assert response.status_code == 200
        assert "任务 'Task X' 状态更新为：完成" in response.json()["message"]
        assert "当前任务：Task Y (待办)" in response.json()["message"]

        # Complete Task Y (Todo -> InProgress)
        response = await client.get("/complete")
        assert response.status_code == 200
        assert "任务 'Task Y' 状态更新为：进行中" in response.json()["message"]
        assert "当前任务：Task Y (进行中)" in response.json()["message"]

        # Complete Task Y (InProgress -> Completed)
        response = await client.get("/complete")
        assert response.status_code == 200
        assert "任务 'Task Y' 状态更新为：完成" in response.json()["message"]
        assert "所有任务已完成！" in response.json()["message"]

        # No more tasks to complete
        response = await client.get("/complete")
        assert response.status_code == 200
        assert "没有待完成的任务。" in response.json()["message"]

@pytest.mark.asyncio
async def test_complete_new_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/update_tasks_new", json={"tasks": [{"content": "Task X", "belong": "user_a"}, {"content": "Task Y", "belong": "user_a"}]})

        # Complete Task X for user_a (Todo -> InProgress)
        response = await client.get("/complete_new/user_a")
        assert response.status_code == 200
        assert "任务 'Task X' 状态更新为：进行中" in response.json()["message"]
        assert "当前任务：Task X (进行中)" in response.json()["message"]

        # Complete Task X for user_a (InProgress -> Completed)
        response = await client.get("/complete_new/user_a")
        assert response.status_code == 200
        assert "任务 'Task X' 状态更新为：完成" in response.json()["message"]
        assert "当前任务：Task Y (待办)" in response.json()["message"]

        # Complete Task Y for user_a (Todo -> InProgress)
        response = await client.get("/complete_new/user_a")
        assert response.status_code == 200
        assert "任务 'Task Y' 状态更新为：进行中" in response.json()["message"]
        assert "当前任务：Task Y (进行中)" in response.json()["message"]

        # Complete Task Y for user_a (InProgress -> Completed)
        response = await client.get("/complete_new/user_a")
        assert response.status_code == 200
        assert "任务 'Task Y' 状态更新为：完成" in response.json()["message"]
        assert "所有任务已完成！" in response.json()["message"]

        # No more tasks to complete for user_a
        response = await client.get("/complete_new/user_a")
        assert response.status_code == 200
        assert "没有待完成的任务。" in response.json()["message"]

@pytest.mark.asyncio
async def test_list_tasks():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/update_tasks", json={"tasks": ["Task L1", "Task L2"]})
        response = await client.get("/list_tasks")
        assert response.status_code == 200
        assert "--- 所有任务状态 ---\n- Task L1: 任务 'Task L1' 的状态是：待办\n- Task L2: 任务 'Task L2' 的状态是：待办\n" in response.json()["message"]

@pytest.mark.asyncio
async def test_list_tasks_new():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/update_tasks_new", json={"tasks": [{"content": "Task N1", "belong": "user_n"}, {"content": "Task N2", "belong": "user_n"}]})
        response = await client.get("/list_tasks_new/user_n")
        assert response.status_code == 200
        assert "--- 用户 'user_n' 的所有任务状态 ---\n- Task N1: 任务 'Task N1' 的状态是：待办\n- Task N2: 任务 'Task N2' 的状态是：待办\n" in response.json()["message"]

@pytest.mark.asyncio
async def test_morning_tasks():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.get("/clear") # Clear existing tasks
        response = await client.get("/morning")
        assert response.status_code == 200
        assert response.json() == {"message": "清晨任务已加载。"}
        response = await client.get("/list_tasks")
        assert "洗澡,刷牙" in response.json()["message"]
        assert "吃早餐" in response.json()["message"]

@pytest.mark.asyncio
async def test_morning_tasks_new():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.get("/clear_new/user_m") # Clear existing tasks for user_m
        response = await client.get("/morning_new/user_m")
        assert response.status_code == 200
        assert response.json() == {"message": "用户 'user_m' 的清晨任务已加载。"}
        response = await client.get("/list_tasks_new/user_m")
        assert "学习Python" in response.json()["message"]
        assert "写文档" in response.json()["message"]

@pytest.mark.asyncio
async def test_clear_tasks():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/update_tasks", json={"tasks": ["Task C1"]})
        response = await client.get("/clear")
        assert response.status_code == 200
        assert response.json() == {"message": "所有老版任务已清空。"}
        response = await client.get("/list_tasks")
        assert "无任务。" in response.json()["message"]

@pytest.mark.asyncio
async def test_clear_new_tasks():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/update_tasks_new", json={"tasks": [{"content": "Task C2", "belong": "user_c"}]})
        response = await client.get("/clear_new/user_c")
        assert response.status_code == 200
        assert response.json() == {"message": "用户 'user_c' 的所有任务已清空。"}
        response = await client.get("/list_tasks_new/user_c")
        assert "无任务。" in response.json()["message"]