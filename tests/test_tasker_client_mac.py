import unittest
from unittest.mock import MagicMock, patch
import os
import requests
import threading
import time

# 导入要测试的模块和 mock 依赖
from src.tasker_client_mac.core import TaskerClient

class TestTaskerClient(unittest.TestCase):
    def setUp(self):
        # 每次测试前重新初始化 TaskerClient，确保测试独立性
        # 并且 mock 掉 requests 模块，防止真正的 HTTP 请求
        self.patcher_requests_post = patch('requests.post')
        self.patcher_requests_get = patch('requests.get')
        self.mock_requests_post = self.patcher_requests_post.start()
        self.mock_requests_get = self.patcher_requests_get.start()

        # Mock 真实的外部依赖
        self.patcher_display = patch('src.tasker_client_mac.core.Display')
        self.patcher_shortcut = patch('src.tasker_client_mac.core.ShortCut')
        self.patcher_kanban_manager = patch('kanbanz.manager.KanBanManager')
        self.patcher_canvas = patch('canvaz.core.Canvas')

        self.mock_display_class = self.patcher_display.start()
        self.mock_shortcut_class = self.patcher_shortcut.start()
        self.mock_kanban_manager_class = self.patcher_kanban_manager.start()
        self.mock_canvas_class = self.patcher_canvas.start()

        # 获取 mock 实例
        self.mock_display_instance = self.mock_display_class.return_value
        self.mock_shortcut_instance = self.mock_shortcut_class.return_value
        self.mock_kanban_manager_instance = self.mock_kanban_manager_class.return_value
        self.mock_canvas_instance = self.mock_canvas_class.return_value

        # 确保 mock 目录存在
        os.makedirs(TaskerClient.CANVAS_DIR, exist_ok=True)

        # Add get_tasks_in to mock_kanban_manager_instance
        self.mock_kanban_manager_instance.get_tasks_in = MagicMock(return_value=[])

        self.client = TaskerClient()

        # Ensure that the TaskerClient's manager and canvas are the mocked instances
        # This is crucial because TaskerClient's __init__ creates new instances if not mocked correctly
        self.client.manager = self.mock_kanban_manager_instance
        self.client.canvas = self.mock_canvas_instance

    def tearDown(self):
        self.patcher_requests_post.stop()
        self.patcher_requests_get.stop()
        self.patcher_display.stop()
        self.patcher_shortcut.stop()
        self.patcher_kanban_manager.stop()
        self.patcher_canvas.stop()

    def test_init(self):
        self.assertEqual(self.client.manager, self.mock_kanban_manager_instance)
        self.assertEqual(self.client.display, self.mock_display_instance)
        self.assertEqual(self.client.shortcut, self.mock_shortcut_instance)
        self.assertEqual(self.client.BASE_URL, os.environ.get("TASKERZ_SERVER_URL", "http://127.0.0.1:8000"))
        self.assertEqual(self.client.KANBAN_PATH, os.environ.get("KANBAN_PATH", "/tmp/mock_kanban.md"))

    def test_update_task(self):
        tasks = [{"content": "Test Task", "belong": "test_user"}]
        self.client._update_task(tasks)
        self.mock_requests_post.assert_called_once_with(
            f"{self.client.BASE_URL}/update_tasks_new", json={"tasks": tasks}
        )
        self.mock_requests_post.return_value.raise_for_status.assert_called_once()

    def test_receive_task(self):
        self.mock_requests_get.return_value.json.return_value = {"message": "Current task: Test Task"}
        response = self.client._receive_task()
        self.mock_requests_get.assert_called_once_with(f"{self.client.BASE_URL}/receive")
        self.assertEqual(response, {"message": "Current task: Test Task"})

    def test_complete_task(self):
        self.mock_requests_get.return_value.json.return_value = {"message": "Task completed."}
        response = self.client._complete_task()
        self.mock_requests_get.assert_called_once_with(f"{self.client.BASE_URL}/complete")
        self.assertEqual(response, {"message": "Task completed."})

    @patch('src.tasker_client_mac.core.threading.Thread')
    @patch('src.tasker_client_mac.core.time.sleep')
    def test_deal_task_a_task(self, mock_sleep, mock_thread):
        # Mock the thread to run immediately for testing purposes
        mock_thread.return_value.start = lambda: self.client._deal_task.target(*self.client._deal_task.args, **self.client._deal_task.kwargs)

        # 使用 mock 实例
        mock_display_dialog = self.mock_display_instance.display_dialog
        mock_run_shortcut = self.mock_shortcut_instance.run_shortcut

        # Test A! task with Pomodoro unit
        task_str = "A!2P My A! Task"
        self.client._deal_task(task_str)

        mock_run_shortcut.assert_called_with("Session", {"task_name": "My A! Task", "duration": 40}) # 2P = 40 minutes
        mock_sleep.assert_called_with(40 * 0.1)
        mock_display_dialog.assert_called_with("任务完成", "任务 'My A! Task' 已完成。", ["OK"], "OK")

        # Test A! task with Minute unit
        mock_run_shortcut.reset_mock()
        mock_sleep.reset_mock()
        mock_display_dialog.reset_mock()
        task_str = "A!15M Another A! Task"
        self.client._deal_task(task_str)
        mock_run_shortcut.assert_called_with("Session", {"task_name": "Another A! Task", "duration": 15})
        mock_sleep.assert_called_with(15 * 0.1)
        mock_display_dialog.assert_called_with("任务完成", "任务 'Another A! Task' 已完成。", ["OK"], "OK")

    def test_deal_task_normal_task(self):
        task_str = "Normal Task Reminder"
        self.client._deal_task(task_str)
        self.mock_display_instance.display_dialog.assert_called_with("任务提醒", task_str, ["OK"], "OK")

    def test_kanban(self):
        self.mock_kanban_manager_instance.sync_ready.return_value = ["Kanban Task 1", "Kanban Task 2"]
        with patch.object(self.client, '_update_task') as mock_update_task:
            response = self.client.kanban()
            self.assertEqual(response, {"message": "successed build"})
            mock_update_task.assert_called_once_with([
                {"content": "Kanban Task 1", "belong": "kanban"},
                {"content": "Kanban Task 2", "belong": "kanban"}
            ])

    def test_add_kanban(self):
        self.mock_kanban_manager_instance.sync_order.return_value = ["Ordered Task 1"]
        with patch.object(self.client, '_update_task') as mock_update_task:
            response = self.client.add_kanban("high")
            self.assertEqual(response, {"message": "successed build"})
            mock_update_task.assert_called_once_with([
                {"content": "Ordered Task 1", "belong": "kanban_priority"}
            ])

    def test_build_flexible_flex(self):
        with patch.object(self.client, '_update_task') as mock_update_task:
            response = self.client.build_flexible("Flex Task", "flex", True)
            self.assertEqual(response, {"message": "successed build"})
            mock_update_task.assert_called_once_with([{"content": "Flex Task", "belong": "flexible"}])

    def test_build_flexible_pool(self):
        self.mock_kanban_manager_instance.get_tasks_in.return_value = ["Pool Task 1", "Pool Task 2"]
        with patch.object(self.client, '_update_task') as mock_update_task:
            response = self.client.build_flexible("My Pool", "pool", True)
            self.assertEqual(response, {"message": "successed build"})
            mock_update_task.assert_called_once_with([
                {"content": "Pool Task 1", "belong": "flexible_pool"},
                {"content": "Pool Task 2", "belong": "flexible_pool"}
            ])

    def test_tips(self):
        response = self.client.tips("category:proj:ques:detail")
        self.assertEqual(response, {"message": "以添加"})
        self.mock_canvas_instance.add_node.assert_called_once_with("category: ques - detail", "0")
        self.mock_canvas_instance.to_file.assert_called_once()

    def test_query_the_current_task(self):
        with patch.object(self.client, '_receive_task', return_value={"message": "Current task: Query Task"}):
            response = self.client.query_the_current_task()
            self.assertEqual(response, {"message": "Current task: Query Task"})

    @patch('src.tasker_client_mac.core.threading.Thread')
    def test_start(self, mock_thread):
        with patch.object(self.client, '_receive_task', return_value={"message": "当前任务：Start Task (待办)"}):
            response = self.client.start()
            self.assertEqual(response, {"message": "task: Start Task 进行中"})
            mock_thread.assert_called_once()
            self.assertEqual(mock_thread.call_args[1]['args'][0], "Start Task")

    def test_close(self):
        with patch.object(self.client, '_complete_task', return_value={"message": "Task closed."}):
            response = self.client.close()
            self.assertEqual(response, {"message": "Task closed."})

    def test_run(self):
        with patch.object(self.client, '_complete_task', return_value={"message": "任务 'Run Task' 状态更新为：完成"}):
            response = self.client.run()
            self.assertEqual(response, {"message": "任务 'Run Task' 状态更新为：完成"})

if __name__ == '__main__':
    unittest.main()