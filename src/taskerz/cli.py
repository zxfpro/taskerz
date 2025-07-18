import argparse
from src.taskerz.workday_facade import WorkdayFacade
from src.taskerz.log import Logger

# 初始化日志
logger = Logger().logger

class CLITaskerzServer:
    """
    命令行接口工具。
    直接调用 WorkdayFacade 的方法，提供手动任务操作功能。
    """
    def __init__(self):
        self.workday_facade = WorkdayFacade()

    def receive_task(self):
        """
        获取当前任务。
        """
        task_info = self.workday_facade.get_current_task_info()
        print(task_info["message"])

    def receive_task_new(self, id: str):
        """
        获取指定用户当前任务。
        """
        task_info = self.workday_facade.get_current_task_info_new(id)
        print(task_info["message"])

    def complete_task(self):
        """
        完成当前任务。
        """
        response = self.workday_facade.complete_current_task()
        print(response["message"])

    def complete_task_new(self, id: str):
        """
        完成指定用户当前任务。
        """
        response = self.workday_facade.complete_current_task_new(id)
        print(response["message"])

    def list_all_tasks(self):
        """
        列出所有老版任务。
        """
        tasks_status = self.workday_facade.get_all_tasks_status()
        message = "---\n所有任务状态 ---\n"
        if not tasks_status:
            message += "无任务。"
        else:
            for task in tasks_status:
                message += f"- {task['name']}: 任务 '{task['name']}' 的状态是：{task['status']}\n"
        print(message)

    def list_all_tasks_new(self, id: str):
        """
        列出指定用户所有任务。
        """
        tasks_status = self.workday_facade.get_all_tasks_status_new(id)
        message = f"---\n用户 '{id}' 的所有任务状态 ---\n"
        if not tasks_status:
            message += "无任务。"
        else:
            for task in tasks_status:
                message += f"- {task['name']}: 任务 '{task['name']}' 的状态是：{task['status']}\n"
        print(message)

    def show_help(self):
        """
        显示帮助信息。
        """
        print("Usage: python cli.py [command] [args]")
        print("Commands:")
        print("  receive             - 获取当前任务")
        print("  receive_new <id>    - 获取指定用户当前任务")
        print("  complete            - 完成当前任务")
        print("  complete_new <id>   - 完成指定用户当前任务")
        print("  list                - 列出所有老版任务")
        print("  list_new <id>       - 列出指定用户所有任务")
        print("  morning             - 加载清晨任务")
        print("  morning_new <id>    - 加载指定用户清晨任务")
        print("  clear               - 清空所有老版任务")
        print("  clear_new <id>      - 清空指定用户所有任务")
        print("  help                - 显示帮助信息")

    def main(self):
        parser = argparse.ArgumentParser(description="Taskerz 命令行工具", add_help=False)
        parser.add_argument("command", nargs="?", help="要执行的命令")
        parser.add_argument("id", nargs="?", help="用户ID (用于新版接口)")
        args = parser.parse_args()

        if args.command == "receive":
            self.receive_task()
        elif args.command == "receive_new":
            if args.id:
                self.receive_task_new(args.id)
            else:
                print("错误: receive_new 命令需要用户ID。")
        elif args.command == "complete":
            self.complete_task()
        elif args.command == "complete_new":
            if args.id:
                self.complete_task_new(args.id)
            else:
                print("错误: complete_new 命令需要用户ID。")
        elif args.command == "list":
            self.list_all_tasks()
        elif args.command == "list_new":
            if args.id:
                self.list_all_tasks_new(args.id)
            else:
                print("错误: list_new 命令需要用户ID。")
        elif args.command == "morning":
            self.workday_facade._morning_tasks()
            print("清晨任务已加载。")
        elif args.command == "morning_new":
            if args.id:
                self.workday_facade._morning_tasks_new(args.id)
                print(f"用户 '{args.id}' 的清晨任务已加载。")
            else:
                print("错误: morning_new 命令需要用户ID。")
        elif args.command == "clear":
            self.workday_facade.clear()
            print("所有老版任务已清空。")
        elif args.command == "clear_new":
            if args.id:
                self.workday_facade.clear_new(args.id)
                print(f"用户 '{args.id}' 的所有任务已清空。")
            else:
                print("错误: clear_new 命令需要用户ID。")
        elif args.command == "help" or not args.command:
            self.show_help()
        else:
            print(f"未知命令: {args.command}")
            self.show_help()

if __name__ == "__main__":
    cli = CLITaskerzServer()
    cli.main()