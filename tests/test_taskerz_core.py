import unittest
import yaml
import os
from unittest.mock import MagicMock, patch
from taskerz.abstra import TaskExecutionStrategy, TaskState
from taskerz.task_state import TodoState, InProgressState, CompletedState, FailedState
from taskerz.execution_strategy import PromptTaskExecutionStrategy
from taskerz.task_manager import Task, Task_new, TaskManager
from taskerz.workday_facade import WorkdayFacade

class TestTaskState(unittest.TestCase):
    def test_todo_state_transition(self):
        state = TodoState()
        mock_context = {"name": "Test Task"}
        self.assertEqual(state.get_status(), "待办")
        new_state = state.complete(mock_context)
        self.assertIsInstance(new_state, InProgressState)

    def test_in_progress_state_transition(self):
        state = InProgressState()
        mock_context = {"name": "Test Task"}
        self.assertEqual(state.get_status(), "进行中")
        new_state = state.complete(mock_context)
        self.assertIsInstance(new_state, CompletedState)

    def test_completed_state_no_transition(self):
        state = CompletedState()
        mock_context = {"name": "Test Task"}
        self.assertEqual(state.get_status(), "完成")
        new_state = state.complete(mock_context)
        self.assertIsInstance(new_state, CompletedState) # Should remain in CompletedState

    def test_failed_state_no_transition(self):
        state = FailedState()
        mock_context = {"name": "Test Task"}
        self.assertEqual(state.get_status(), "失败")
        new_state = state.complete(mock_context)
        self.assertIsInstance(new_state, FailedState) # Should remain in FailedState

class TestTask(unittest.TestCase):
    def setUp(self):
        # 强制重新加载模块以避免导入问题
        import importlib
        import src.taskerz.task_state
        import src.taskerz.task_manager
        importlib.reload(src.taskerz.task_state)
        importlib.reload(src.taskerz.task_manager)
        from src.taskerz.task_state import TodoState
        from src.taskerz.task_manager import Task
        from src.taskerz.execution_strategy import PromptTaskExecutionStrategy
        self.TodoState = TodoState
        self.Task = Task
        self.PromptTaskExecutionStrategy = PromptTaskExecutionStrategy

    def test_task_initialization(self):
        task = self.Task("My Task")
        self.assertEqual(task.name, "My Task")
        self.assertIsInstance(task._state, self.TodoState)
        self.assertIsInstance(task.execution_strategy, self.PromptTaskExecutionStrategy)

    def test_task_request(self):
        task = Task("My Task")
        with patch('src.taskerz.execution_strategy.PromptTaskExecutionStrategy.execute', return_value="Mock Prompt") as mock_execute:
            prompt = task.request()
            self.assertEqual(prompt, "Mock Prompt")
            mock_execute.assert_called_once_with({"name": "My Task", "script_code": ""})

    def test_task_complete(self):
        task = Task("My Task")
        self.assertEqual(task.get_status(), "待办")
        task.complete_task()
        self.assertEqual(task.get_status(), "进行中")
        task.complete_task()
        self.assertEqual(task.get_status(), "完成")

class TestTaskNew(unittest.TestCase):
    def setUp(self):
        # 强制重新加载模块以避免导入问题
        import importlib
        import src.taskerz.task_state
        import src.taskerz.task_manager
        importlib.reload(src.taskerz.task_state)
        importlib.reload(src.taskerz.task_manager)
        from src.taskerz.task_state import TodoState
        from src.taskerz.task_manager import Task_new
        from src.taskerz.execution_strategy import PromptTaskExecutionStrategy
        self.TodoState = TodoState
        self.Task_new = Task_new
        self.PromptTaskExecutionStrategy = PromptTaskExecutionStrategy

    def test_task_new_initialization(self):
        task = self.Task_new("My New Task", "user1")
        self.assertEqual(task.name, "My New Task")
        self.assertEqual(task.belong, "user1")
        self.assertIsInstance(task._state, self.TodoState)
        self.assertIsInstance(task.execution_strategy, self.PromptTaskExecutionStrategy)

    def test_task_new_request(self):
        task = Task_new("My New Task", "user1")
        with patch('src.taskerz.execution_strategy.PromptTaskExecutionStrategy.execute', return_value="Mock New Prompt") as mock_execute:
            prompt = task.request()
            self.assertEqual(prompt, "Mock New Prompt")
            mock_execute.assert_called_once_with({"name": "My New Task", "belong": "user1", "script_code": ""})

    def test_task_new_complete(self):
        task = Task_new("My New Task", "user1")
        self.assertEqual(task.get_status(), "待办")
        task.complete_task()
        self.assertEqual(task.get_status(), "进行中")
        task.complete_task()
        self.assertEqual(task.get_status(), "完成")

    def test_task_new_equality(self):
        task1 = Task_new("Task A", "user1")
        task2 = Task_new("Task A", "user1")
        task3 = Task_new("Task B", "user1")
        task4 = Task_new("Task A", "user2")
        self.assertEqual(task1, task2)
        self.assertNotEqual(task1, task3)
        self.assertNotEqual(task1, task4)

    def test_task_new_hash(self):
        task1 = Task_new("Task A", "user1")
        task2 = Task_new("Task A", "user1")
        self.assertEqual(hash(task1), hash(task2))

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        # 每次测试前清空 TaskManager 实例，确保测试独立性
        TaskManager._instance = None
        self.task_manager = TaskManager()

    def test_singleton(self):
        manager1 = TaskManager()
        manager2 = TaskManager()
        self.assertIs(manager1, manager2)

    def test_add_task(self):
        self.assertTrue(self.task_manager.add_task("Task1"))
        self.assertFalse(self.task_manager.add_task("Task1")) # Cannot add duplicate
        self.assertEqual(len(self.task_manager._tasks_order), 1)
        self.assertIn("Task1", self.task_manager._tasks)

    def test_add_task_new(self):
        self.assertTrue(self.task_manager.add_task_new({"content": "New Task1", "belong": "userA"}))
        self.assertFalse(self.task_manager.add_task_new({"content": "New Task1", "belong": "userA"})) # Cannot add duplicate
        self.assertIn("userA", self.task_manager._tasks_new)
        self.assertEqual(len(self.task_manager._tasks_new["userA"]), 1)

    def test_get_current_sequential_task(self):
        self.task_manager.add_task("Task1")
        self.task_manager.add_task("Task2")
        current_task = self.task_manager.get_current_sequential_task()
        self.assertEqual(current_task.name, "Task1")
        current_task.complete_task() # Task1 -> InProgress
        current_task = self.task_manager.get_current_sequential_task()
        self.assertEqual(current_task.name, "Task1") # Still Task1
        current_task.complete_task() # Task1 -> Completed
        current_task = self.task_manager.get_current_sequential_task()
        self.assertEqual(current_task.name, "Task2") # Now Task2

    def test_get_current_sequential_task_new(self):
        self.task_manager.add_task_new({"content": "New Task1", "belong": "userA"})
        self.task_manager.add_task_new({"content": "New Task2", "belong": "userA"})
        self.task_manager.add_task_new({"content": "New Task3", "belong": "userB"})

        current_task_a = self.task_manager.get_current_sequential_task_new("userA")
        self.assertEqual(current_task_a.name, "New Task1")
        current_task_a.complete_task() # New Task1 -> InProgress
        current_task_a = self.task_manager.get_current_sequential_task_new("userA")
        self.assertEqual(current_task_a.name, "New Task1") # Still New Task1
        current_task_a.complete_task() # New Task1 -> Completed
        current_task_a = self.task_manager.get_current_sequential_task_new("userA")
        self.assertEqual(current_task_a.name, "New Task2") # Now New Task2

        current_task_b = self.task_manager.get_current_sequential_task_new("userB")
        self.assertEqual(current_task_b.name, "New Task3")

    def test_complete_current_task(self):
        self.task_manager.add_task("Task1")
        self.task_manager.add_task("Task2")
        self.assertTrue(self.task_manager.complete_current_task()) # Task1 -> InProgress
        self.assertEqual(self.task_manager.get_task("Task1").get_status(), "进行中")
        self.assertTrue(self.task_manager.complete_current_task()) # Task1 -> Completed
        self.assertEqual(self.task_manager.get_task("Task1").get_status(), "完成")
        self.assertTrue(self.task_manager.complete_current_task()) # Task2 -> InProgress
        self.assertEqual(self.task_manager.get_task("Task2").get_status(), "进行中")
        self.assertTrue(self.task_manager.complete_current_task()) # Task2 -> Completed
        self.assertEqual(self.task_manager.get_task("Task2").get_status(), "完成")
        self.assertFalse(self.task_manager.complete_current_task()) # No more tasks

    def test_complete_current_task_new(self):
        self.task_manager.add_task_new({"content": "New Task1", "belong": "userA"})
        self.task_manager.add_task_new({"content": "New Task2", "belong": "userA"})
        self.assertTrue(self.task_manager.complete_current_task_new("userA")) # New Task1 -> InProgress
        self.assertEqual(self.task_manager.get_task_status_new({"content": "New Task1", "belong": "userA"}), "进行中")
        self.assertTrue(self.task_manager.complete_current_task_new("userA")) # New Task1 -> Completed
        self.assertEqual(self.task_manager.get_task_status_new({"content": "New Task1", "belong": "userA"}), "完成")
        self.assertTrue(self.task_manager.complete_current_task_new("userA")) # New Task2 -> InProgress
        self.assertEqual(self.task_manager.get_task_status_new({"content": "New Task2", "belong": "userA"}), "进行中")
        self.assertTrue(self.task_manager.complete_current_task_new("userA")) # New Task2 -> Completed
        self.assertEqual(self.task_manager.get_task_status_new({"content": "New Task2", "belong": "userA"}), "完成")
        self.assertFalse(self.task_manager.complete_current_task_new("userA")) # No more tasks for userA

    def test_get_task_list(self):
        self.task_manager.add_task("Task1")
        self.task_manager.add_task("Task2")
        task_list = self.task_manager.get_task_list()
        self.assertEqual(len(task_list), 2)
        self.assertEqual(task_list[0]["name"], "Task1")
        self.assertEqual(task_list[0]["status"], "待办")

    def test_get_task_list_new(self):
        self.task_manager.add_task_new({"content": "New Task1", "belong": "userA"})
        self.task_manager.add_task_new({"content": "New Task2", "belong": "userA"})
        self.task_manager.add_task_new({"content": "New Task3", "belong": "userB"})
        task_list_a = self.task_manager.get_task_list_new("userA")
        self.assertEqual(len(task_list_a), 2)
        self.assertEqual(task_list_a[0]["name"], "New Task1")
        self.assertEqual(task_list_a[0]["status"], "待办")
        task_list_b = self.task_manager.get_task_list_new("userB")
        self.assertEqual(len(task_list_b), 1)
        self.assertEqual(task_list_b[0]["name"], "New Task3")

    def test_clear(self):
        self.task_manager.add_task("Task1")
        self.task_manager.clear()
        self.assertEqual(len(self.task_manager._tasks_order), 0)
        self.assertEqual(len(self.task_manager._tasks), 0)

    def test_clear_new(self):
        self.task_manager.add_task_new({"content": "New Task1", "belong": "userA"})
        self.task_manager.add_task_new({"content": "New Task2", "belong": "userB"})
        self.task_manager.clear_new("userA")
        self.assertNotIn("userA", self.task_manager._tasks_new)
        self.assertIn("userB", self.task_manager._tasks_new)
        self.task_manager.clear_new() # Clear all
        self.assertEqual(len(self.task_manager._tasks_new), 0)

class TestWorkdayFacade(unittest.TestCase):
    def setUp(self):
        # 每次测试前清空 TaskManager 实例，确保测试独立性
        TaskManager._instance = None
        self.workday_facade = WorkdayFacade()

    def test_get_current_task_info(self):
        self.workday_facade.clear() # Ensure no tasks initially
        info = self.workday_facade.get_current_task_info()
        self.assertEqual(info["message"], "所有任务已完成！")

        self.workday_facade.add_person_tasks(["Task A"])
        info = self.workday_facade.get_current_task_info()
        self.assertIn("name", info)
        self.assertEqual(info["name"], "Task A")
        self.assertEqual(info["status"], "待办")

    def test_complete_current_task(self):
        self.workday_facade.clear()
        self.workday_facade.add_person_tasks(["Task A", "Task B"])
        response = self.workday_facade.complete_current_task()
        self.assertIn("任务 'Task A' 状态更新为：进行中", response["message"])
        self.assertIn("当前任务：Task A (进行中)", response["message"]) # Still Task A

        response = self.workday_facade.complete_current_task()
        self.assertIn("任务 'Task A' 状态更新为：完成", response["message"])
        self.assertIn("当前任务：Task B (待办)", response["message"]) # Now Task B

    def test_morning_tasks(self):
        # 创建临时的 workday_tasks.yaml 文件
        test_yaml_content = {
            "morning_tasks": [
                {"content": "Test Task 1"},
                {"content": "Test Task 2"}
            ]
        }
        with open("workday_tasks.yaml", "w", encoding="utf-8") as f:
            yaml.dump(test_yaml_content, f)

        self.workday_facade.clear()
        self.workday_facade._morning_tasks()
        tasks = self.workday_facade.get_all_tasks_status()
        self.assertEqual(len(tasks), 2) # 期望加载 2 个任务
        self.assertEqual(tasks[0]["name"], "Test Task 1")
        self.assertEqual(tasks[1]["name"], "Test Task 2")

        # 清理临时文件
        os.remove("workday_tasks.yaml")
        # 移除旧的断言，因为现在是基于临时文件内容进行断言
        # self.assertEqual(tasks[0]["name"], "洗澡,刷牙")

    def test_morning_tasks_new(self):
        # 创建临时的 workday_tasks_new.yaml 文件
        test_yaml_content_new = {
            "morning_tasks_new": {
                "user_a": [
                    {"content": "New Test Task 1"},
                    {"content": "New Test Task 2"}
                ]
            }
        }
        with open("workday_tasks_new.yaml", "w", encoding="utf-8") as f:
            yaml.dump(test_yaml_content_new, f)

        self.workday_facade.clear_new()
        self.workday_facade._morning_tasks_new("user_a")
        tasks = self.workday_facade.get_all_tasks_status_new("user_a")
        self.assertEqual(len(tasks), 2) # 期望加载 2 个任务
        self.assertEqual(tasks[0]["name"], "New Test Task 1")
        self.assertEqual(tasks[1]["name"], "New Test Task 2")

        # 清理临时文件
        os.remove("workday_tasks_new.yaml")
        # 移除旧的断言，因为现在是基于临时文件内容进行断言
        # self.assertEqual(tasks[0]["name"], "学习Python")

    def test_add_person_tasks_new(self):
        self.workday_facade.clear_new("user_test")
        self.workday_facade.add_person_tasks_new([{"content": "Test Task1", "belong": "user_test"}])
        tasks = self.workday_facade.get_all_tasks_status_new("user_test")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["name"], "Test Task1")
        self.assertEqual(tasks[0]["belong"], "user_test")

if __name__ == '__main__':
    unittest.main()