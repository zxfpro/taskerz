from src.taskerz.abstra import TaskState

class TodoState(TaskState):
    """
    待办状态。
    """
    def handle(self, task_context: dict):
        """
        处理待办任务。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 处于待办状态。")

    def complete(self, task_context: dict):
        """
        将待办任务推进到进行中状态。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 状态更新为：进行中")
        return InProgressState()

    def get_status(self) -> str:
        """
        获取状态字符串。
        """
        return "待办"

class InProgressState(TaskState):
    """
    进行中状态。
    """
    def handle(self, task_context: dict):
        """
        处理进行中任务。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 处于进行中状态。")

    def complete(self, task_context: dict):
        """
        将进行中任务推进到已完成状态。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 状态更新为：完成")
        return CompletedState()

    def get_status(self) -> str:
        """
        获取状态字符串。
        """
        return "进行中"

class CompletedState(TaskState):
    """
    已完成状态。
    """
    def handle(self, task_context: dict):
        """
        处理已完成任务。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 已完成。")

    def complete(self, task_context: dict):
        """
        已完成任务无法再次完成。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 已经完成，无法再次完成。")
        return self

    def get_status(self) -> str:
        """
        获取状态字符串。
        """
        return "完成"

class FailedState(TaskState):
    """
    失败状态。
    """
    def handle(self, task_context: dict):
        """
        处理失败任务。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 失败。")

    def complete(self, task_context: dict):
        """
        失败任务无法再次完成。
        """
        task_name = task_context.get("name", "未知任务")
        print(f"任务 '{task_name}' 失败，无法再次完成。")
        return self

    def get_status(self) -> str:
        """
        获取状态字符串。
        """
        return "失败"