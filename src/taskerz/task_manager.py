from src.taskerz.abstra import TaskState, TaskExecutionStrategy
from src.taskerz.task_state import TodoState, InProgressState, CompletedState, FailedState
from src.taskerz.execution_strategy import PromptTaskExecutionStrategy

class Task:
    """
    任务类（老版，无 belong 字段）。
    """
    def __init__(self, name: str, script_code: str = "", execution_strategy: TaskExecutionStrategy = None):
        self.name = name
        self.script_code = script_code
        self._state: TaskState = TodoState()
        self.execution_strategy = execution_strategy if execution_strategy else PromptTaskExecutionStrategy()

    def set_state(self, state: TaskState):
        """
        设置任务状态。
        """
        self._state = state

    def request(self) -> str:
        """
        请求任务执行，获取提示。
        """
        return self.execution_strategy.execute({"name": self.name, "script_code": self.script_code})

    def complete_task(self):
        """
        完成任务，推进状态。
        """
        self._state = self._state.complete({"name": self.name, "script_code": self.script_code})

    def get_status(self) -> str:
        """
        获取任务当前状态的字符串表示。
        """
        return self._state.get_status()

class Task_new:
    """
    任务类（新版，带 belong 字段，支持多用户/配置隔离）。
    """
    def __init__(self, name: str, belong: str, script_code: str = "", execution_strategy: TaskExecutionStrategy = None):
        self.name = name
        self.belong = belong
        self.script_code = script_code
        self._state: TaskState = TodoState()
        self.execution_strategy = execution_strategy if execution_strategy else PromptTaskExecutionStrategy()

    def set_state(self, state: TaskState):
        """
        设置任务状态。
        """
        self._state = state

    def request(self) -> str:
        """
        请求任务执行，获取提示。
        """
        return self.execution_strategy.execute({"name": self.name, "belong": self.belong, "script_code": self.script_code})

    def complete_task(self):
        """
        完成任务，推进状态。
        """
        self._state = self._state.complete({"name": self.name, "belong": self.belong, "script_code": self.script_code})

    def get_status(self) -> str:
        """
        获取任务当前状态的字符串表示。
        """
        return self._state.get_status()

    def __eq__(self, other):
        if not isinstance(other, Task_new):
            return NotImplemented
        return self.name == other.name and self.belong == other.belong

    def __hash__(self):
        return hash((self.name, self.belong))

class TaskManager:
    """
    核心任务管理模块。
    维护任务队列和字典，支持新旧任务类型。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._tasks_order = []  # 保持任务顺序
            cls._instance._tasks = {}  # 通过名称快速查找任务
            cls._instance._tasks_new = {} # 新版任务，按belong分类
        return cls._instance

    def clear(self):
        """
        清空所有老版任务。
        """
        self._tasks_order = []
        self._tasks = {}

    def clear_new(self, belong: str = None):
        """
        清空所有新版任务，如果指定 belong 则清空对应分类下的任务。
        """
        if belong:
            if belong in self._tasks_new:
                del self._tasks_new[belong]
        else:
            self._tasks_new = {}

    def add_task(self, task_name: str, script_code: str = ""):
        """
        添加一个老版任务。
        """
        if task_name not in self._tasks:
            task = Task(task_name, script_code)
            self._tasks_order.append(task)
            self._tasks[task_name] = task
            return True
        return False

    def add_task_new(self, task_info: dict):
        """
        添加一个新版任务。
        task_info 示例: {"content": "学习Python", "belong": "user_a"}
        """
        name = task_info.get("content")
        belong = task_info.get("belong")
        if not name or not belong:
            return False

        if belong not in self._tasks_new:
            self._tasks_new[belong] = []

        task = Task_new(name, belong)
        if task not in self._tasks_new[belong]:
            self._tasks_new[belong].append(task)
            return True
        return False

    def get_task(self, task_name: str) -> Task:
        """
        根据任务名称获取老版任务。
        """
        return self._tasks.get(task_name)

    def get_current_sequential_task(self) -> Task:
        """
        获取当前第一个未完成的老版任务。
        """
        for task in self._tasks_order:
            if task.get_status() != "完成":
                return task
        return None

    def get_current_sequential_task_new(self, belong: str) -> Task_new:
        """
        获取指定 belong 下当前第一个未完成的新版任务。
        """
        if belong in self._tasks_new:
            for task in self._tasks_new[belong]:
                if task.get_status() != "完成":
                    return task
        return None

    def complete_current_task(self):
        """
        完成当前第一个未完成的老版任务。
        """
        current_task = self.get_current_sequential_task()
        if current_task:
            current_task.complete_task()
            return True
        return False

    def complete_current_task_new(self, belong: str):
        """
        完成指定 belong 下当前第一个未完成的新版任务。
        """
        current_task = self.get_current_sequential_task_new(belong)
        if current_task:
            current_task.complete_task()
            return True
        return False

    def get_task_status(self, task_name: str) -> str:
        """
        获取老版任务的状态。
        """
        task = self.get_task(task_name)
        return task.get_status() if task else "任务不存在"

    def get_task_status_new(self, task_info: dict) -> str:
        """
        获取新版任务的状态。
        task_info 示例: {"content": "学习Python", "belong": "user_a"}
        """
        name = task_info.get("content")
        belong = task_info.get("belong")
        if not name or not belong or belong not in self._tasks_new:
            return "任务不存在或 belong 不存在"

        target_task = Task_new(name, belong)
        for task in self._tasks_new[belong]:
            if task == target_task:
                return task.get_status()
        return "任务不存在"

    def get_task_list(self) -> list:
        """
        获取所有老版任务的状态列表。
        """
        return [{"name": task.name, "status": task.get_status()} for task in self._tasks_order]

    def get_task_list_new(self, belong: str) -> list:
        """
        获取指定 belong 下所有新版任务的状态列表。
        """
        if belong in self._tasks_new:
            return [{"name": task.name, "belong": task.belong, "status": task.get_status()} for task in self._tasks_new[belong]]
        return []