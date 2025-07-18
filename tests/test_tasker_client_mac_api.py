import pytest
from httpx import AsyncClient
from tasker_client_mac.server import app
from tasker_client_mac.core import TaskerClient
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="function", autouse=True)
def mock_tasker_client():
    """
    为每个测试用例 mock TaskerClient 实例，确保测试独立性。
    """
    with patch('src.tasker_client_mac.server.TaskerClient') as MockTaskerClient:
        instance = MockTaskerClient.return_value
        yield instance

@pytest.mark.asyncio
async def test_build_kanban(mock_tasker_client):
    mock_tasker_client.kanban.return_value = {"message": "successed build"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/build_kanban")
        assert response.status_code == 200
        assert response.json() == {"message": "successed build"}
        mock_tasker_client.kanban.assert_called_once()

@pytest.mark.asyncio
async def test_add_kanban(mock_tasker_client):
    mock_tasker_client.add_kanban.return_value = {"message": "successed build"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/add_kanban")
        assert response.status_code == 200
        assert response.json() == {"message": "successed build"}
        mock_tasker_client.add_kanban.assert_called_once()

@pytest.mark.asyncio
async def test_build_flexible(mock_tasker_client):
    mock_tasker_client.build_flexible.return_value = {"message": "successed build"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {"task": "New Task", "type": "flex", "action": True}
        response = await client.post("/build_flexible", json=request_data)
        assert response.status_code == 200
        assert response.json() == {"message": "successed build"}
        mock_tasker_client.build_flexible.assert_called_once_with("New Task", "flex", True)

@pytest.mark.asyncio
async def test_tips(mock_tasker_client):
    mock_tasker_client.tips.return_value = {"message": "以添加"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {"task": "delay:proj:ques:detail"}
        response = await client.post("/tips", json=request_data)
        assert response.status_code == 200
        assert response.json() == {"message": "以添加"}
        mock_tasker_client.tips.assert_called_once_with("delay:proj:ques:detail")

@pytest.mark.asyncio
async def test_receive(mock_tasker_client):
    mock_tasker_client.query_the_current_task.return_value = {"message": "当前任务：Test Task (待办)"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/receive")
        assert response.status_code == 200
        assert response.json() == {"message": "当前任务：Test Task (待办)"}
        mock_tasker_client.query_the_current_task.assert_called_once()

@pytest.mark.asyncio
async def test_start(mock_tasker_client):
    mock_tasker_client.start.return_value = {"message": "task: Test Task 进行中"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/start")
        assert response.status_code == 200
        assert response.json() == {"message": "task: Test Task 进行中"}
        mock_tasker_client.start.assert_called_once()

@pytest.mark.asyncio
async def test_close(mock_tasker_client):
    mock_tasker_client.close.return_value = {"message": "task: Test Task 已完成"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/close")
        assert response.status_code == 200
        assert response.json() == {"message": "task: Test Task 已完成"}
        mock_tasker_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_run(mock_tasker_client):
    mock_tasker_client.run.return_value = {"message": "任务 'Test Task' 状态更新为：进行中"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/run")
        assert response.status_code == 200
        assert response.json() == {"message": "任务 'Test Task' 状态更新为：进行中"}
        mock_tasker_client.run.assert_called_once()