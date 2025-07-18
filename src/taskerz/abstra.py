from abc import ABC, abstractmethod

class TaskExecutionStrategy(ABC):
    """
    抽象任务执行策略基类。
    定义了任务执行的接口。
    """
    @abstractmethod
    def execute(self, task_context: dict):
        """
        执行任务。
        :param task_context: 任务上下文，包含任务相关信息。
        """
        pass

class TaskState(ABC):
    """
    抽象任务状态基类。
    定义了任务状态的行为接口。
    """
    @abstractmethod
    def handle(self, task_context: dict):
        """
        处理当前状态下的任务。
        :param task_context: 任务上下文。
        """
        pass

    @abstractmethod
    def complete(self, task_context: dict):
        """
        完成当前状态下的任务，并可能触发状态转换。
        :param task_context: 任务上下文。
        :return: 新的任务状态实例，如果状态未改变则返回自身。
        """
        pass

    @abstractmethod
    def get_status(self) -> str:
        """
        获取当前状态的字符串表示。
        :return: 状态字符串。
        """
        pass