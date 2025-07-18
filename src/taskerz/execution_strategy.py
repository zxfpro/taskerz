from src.taskerz.abstra import TaskExecutionStrategy

class PromptTaskExecutionStrategy(TaskExecutionStrategy):
    """
    人工提示型任务执行策略。
    在执行时提供一个提示信息。
    """
    def execute(self, task_context: dict):
        """
        执行人工提示型任务，返回一个 mock 提示。
        :param task_context: 任务上下文，包含任务名称等信息。
        :return: 任务提示字符串。
        """
        task_name = task_context.get("name", "未知任务")
        description = task_context.get("description", "无描述")
        due_date = task_context.get("due_date", "无截止日期")
        priority = task_context.get("priority", "无优先级")
        return (
            f"任务名称：{task_name}\n"
            f"描述：{description}\n"
            f"截止日期：{due_date}\n"
            f"优先级：{priority}\n"
            f"请根据以上信息开始执行任务。"
        )