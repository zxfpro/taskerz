import requests
import threading
import time
import re
import os

# 导入真实外部依赖
try:
    from appscriptz.core import Display, ShortCut
except ImportError:
    print("Warning: appscriptz not available. Using mock Display and ShortCut.")
    class Display:
        def display_dialog(self, title, text, buttons, button_cancel):
            print(f"Mock Display Dialog: Title='{title}', Text='{text}', Buttons={buttons}, Cancel='{button_cancel}'")
            return {"button_returned": buttons[0], "text_returned": ""}
    class ShortCut:
        def run_shortcut(self, shortcut_name, params):
            print(f"Mock ShortCut: Running '{shortcut_name}' with params: {params}")
            if shortcut_name == "Session":
                return "Mock Session Output"
            elif shortcut_name == "ProgressNote":
                return "Mock Progress Note"
            return "Mock Shortcut Output"

from kanbanz.manager import KanBanManager
from canvaz.core import Canvas

class MockCanvas:
    def __init__(self, file_path=None):
        print(f"MockCanvas initialized with file_path: {file_path}")
        self.file_path = file_path
        self.nodes = []

    def add_node(self, text, x, y=0):
        print(f"MockCanvas: Adding node '{text}' at ({x}, {y})")
        self.nodes.append({"text": text, "x": x, "y": y})

    def to_file(self):
        print(f"MockCanvas: Saving to file {self.file_path}")
        # Simulate writing to a file
        pass

    def select_nodes_by_text(self, text):
        # Mock implementation for select_nodes_by_text
        print(f"MockCanvas: Selecting nodes by text '{text}'")
        return [{"id": "mock_node_id", "text": text}] # Return a mock node

# 辅助函数
def task_with_time(task_name: str, duration_minutes: int):
    """模拟带时间的任务执行"""
    print(f"开始任务 '{task_name}'，预计持续 {duration_minutes} 分钟。")
    ShortCut().run_shortcut("Session", {"task_name": task_name, "duration": duration_minutes})
    time.sleep(duration_minutes * 0.1)  # 模拟耗时，实际应为真实耗时
    print(f"任务 '{task_name}' 模拟完成。")
    return True

def failed_safe(func, *args, **kwargs):
    """带失败保护的函数执行"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"函数执行失败: {e}")
        return None

class TaskerClient:
    """
    核心业务逻辑与编排模块。
    封装了与 taskerz 服务端 API 的 HTTP 交互。
    根据从服务端获取的任务信息，判断任务类型（A! 或普通提醒），并调用 _deal_task() 进行差异化处理。
    """
    BASE_URL = os.environ.get("TASKERZ_SERVER_URL", "http://127.0.0.1:8000")
    KANBAN_PATH = os.environ.get("KANBAN_PATH", "/tmp/mock_kanban.md") # Mock path
    CANVAS_DIR = os.environ.get("CANVAS_DIR", "/tmp/mock_canvas") # Mock dir

    def __init__(self):
        self.pathlibs = []  # 存储 Canvas 文件路径
        self.pathlibs_dict = {} # 映射项目名称到 Canvas 文件路径
        self.manager = KanBanManager(self.KANBAN_PATH, pathlib=[]) # 假设 pathlib=True 表示传入的是路径
        self.display = Display()
        self.shortcut = ShortCut()
        os.makedirs(self.CANVAS_DIR, exist_ok=True) # 确保目录存在

    def kanban(self):
        """
        自动同步 Obsidian 看板任务，并更新到服务端。
        """
        print("Mock: Building kanban...")
        ready_tasks = self.manager.sync_ready()
        if ready_tasks:
            self._update_task([{"content": task, "belong": "kanban"} for task in ready_tasks])
            print(f"Mock: Synced {len(ready_tasks)} tasks from kanban.")
        else:
            print("Mock: No ready tasks in kanban.")
        return {"message": "successed build"}

    def add_kanban(self, p: str = None):
        """
        手动同步 Obsidian 看板任务（带优先级），并更新到服务端。
        """
        print(f"Mock: Adding kanban with priority {p}...")
        ordered_tasks = self.manager.sync_order(p)
        if ordered_tasks:
            self._update_task([{"content": task, "belong": "kanban_priority"} for task in ordered_tasks])
            print(f"Mock: Added {len(ordered_tasks)} tasks from kanban with priority.")
        else:
            print("Mock: No ordered tasks in kanban.")
        return {"message": "successed build"}

    def build_flexible(self, task: str, type: str, action: bool):
        """
        灵活添加指定任务或从特定池任务，并更新到服务端。
        """
        print(f"Mock: Building flexible task: {task}, type: {type}, action: {action}")
        if action:
            if type == "flex":
                self._update_task([{"content": task, "belong": "flexible"}])
            elif type == "pool":
                pool_tasks = self.manager.get_tasks_in(task)
                self._update_task([{"content": t, "belong": "flexible_pool"} for t in pool_tasks])
            print("Mock: Flexible build success.")
        return {"message": "successed build"}

    def tips(self, task: str):
        """
        在本地 Obsidian Canvas 文件中添加带分类和颜色的提示/备注。
        """
        print(f"Mock: Adding tips for task: {task}")
        parts = task.split(":")
        if len(parts) >= 4:
            category, project, question, detail = parts[0], parts[1], parts[2], parts[3]
            canvas_file = os.path.join(self.CANVAS_DIR, f"{project}.canvas")
            self.canvas.file_path = canvas_file # Update the file_path of the mocked canvas instance
            node_content = f"{category}: {question} - {detail}"
            self.canvas.add_node(node_content, "0") # 默认灰色
            self.canvas.to_file() # to_file no longer needs canvas_file as argument
            print("Tips added to Canvas.")
        return {"message": "以添加"}

    def _update_task(self, tasks: list):
        """
        向服务端批量更新任务。
        """
        print(f"Mock: Updating tasks to server: {tasks}")
        try:
            response = requests.post(f"{self.BASE_URL}/update_tasks_new", json={"tasks": tasks})
            response.raise_for_status()
            print(f"Mock: Server response: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Mock: Error updating tasks to server: {e}")

    def _receive_task(self) -> dict:
        """
        从服务端获取当前任务。
        """
        print("Mock: Receiving task from server...")
        try:
            response = requests.get(f"{self.BASE_URL}/receive")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Mock: Error receiving task from server: {e}")
            return {"message": "Error: Could not connect to server."}

    def _complete_task(self) -> dict:
        """
        向服务端发送完成当前任务的请求。
        """
        print("Mock: Completing task on server...")
        try:
            response = requests.get(f"{self.BASE_URL}/complete")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Mock: Error completing task on server: {e}")
            return {"message": "Error: Could not connect to server."}

    def _deal_task(self, task_str: str):
        """
        处理任务字符串，根据 A! 标记执行本地自动化。
        """
        print(f"Mock: Dealing with task: {task_str}")
        if task_str.startswith("A!"):
            match = re.match(r"A!(\d+)([PM])\s(.+)", task_str)
            if match:
                duration_val = int(match.group(1))
                duration_unit = match.group(2)
                task_name = match.group(3).strip()

                duration_minutes = duration_val
                if duration_unit == "P": # 假设 P 代表 20 分钟一个 Pomodoro
                    duration_minutes *= 20

                print(f"Mock: Detected A! task: {task_name}, Duration: {duration_minutes} minutes.")

                # 模拟执行任务
                if failed_safe(task_with_time, task_name, duration_minutes):
                    self.display.display_dialog("任务完成", f"任务 '{task_name}' 已完成。", ["OK"], "OK")
                    # 模拟更新 Canvas 节点颜色
                    canvas_file = os.path.join(self.CANVAS_DIR, "default.canvas") # 假设有一个默认 canvas
                    canvas = MockCanvas(canvas_file)
                    nodes = canvas.select_nodes_by_text(task_name)
                    if nodes:
                        node_id = nodes[0]["id"]
                        # 模拟更新节点颜色为完成状态 (例如 "4")
                        print(f"Mock: Updating Canvas node {node_id} for '{task_name}' to color '4'.")
                    else:
                        print(f"Mock: Canvas node for '{task_name}' not found.")
                else:
                    self.display.display_dialog("任务失败", f"任务 '{task_name}' 执行失败。", ["OK"], "OK")
            else:
                print("Mock: A! 任务格式不匹配。")
        else:
            print(f"Mock: 普通任务提醒: {task_str}")
            self.display.display_dialog("任务提醒", task_str, ["OK"], "OK")

    def query_the_current_task(self) -> dict:
        """
        从服务端查询当前任务信息。
        """
        return self._receive_task()

    def start(self):
        """
        启动当前待办任务，如果是 A! 任务则触发本地自动化流程。
        """
        print("Mock: Starting task...")
        task_info = self._receive_task()
        if "message" in task_info and task_info["message"].startswith("当前任务："):
            task_str = task_info["message"].split("当前任务：")[1].split(" (")[0]
            threading.Thread(target=self._deal_task, args=(task_str,)).start()
            return {"message": f"task: {task_str} 进行中"}
        return task_info

    def close(self):
        """
        关闭当前进行中任务，触发本地清理并同步到服务端。
        """
        print("Mock: Closing task...")
        response = self._complete_task()
        return response

    def run(self):
        """
        推进当前任务状态，对于 A! 任务会触发本地自动化，并同步状态。
        """
        print("Mock: Running task...")
        response = self._complete_task()
        if "message" in response and response["message"].startswith("任务 '"):
            # 假设完成任务后，服务端会返回下一个任务信息，这里简化处理
            # 实际可能需要再次调用 _receive_task 来获取下一个任务并处理
            print(f"Mock: Task completed, server response: {response['message']}")
            # 如果有下一个任务，可以再次调用 _deal_task
            # task_info = self._receive_task()
            # if "message" in task_info and task_info["message"].startswith("当前任务："):
            #     task_str = task_info["message"].split("当前任务：")[1].split(" (")[0]
            #     threading.Thread(target=self._deal_task, args=(task_str,)).start()
        return response
