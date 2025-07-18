import yaml
from src.taskerz.task_manager import TaskManager

class WorkdayFacade:
    """
    外观模式实现。
    为外部模块提供简化、统一的任务操作接口，封装了与 TaskManager 的交互。
    负责从 YAML 配置文件加载预设任务，并将其添加到 TaskManager。
    """
    def __init__(self):
        self.task_manager = TaskManager()
        self.workday_tasks_yaml_path = "workday_tasks.yaml"
        self.workday_tasks_new_yaml_path = "workday_tasks_new.yaml"

    def clear(self):
        """
        清空所有老版任务。
        """
        self.task_manager.clear()

    def clear_new(self, id: str = None):
        """
        清空所有新版任务，如果指定 id 则清空对应分类下的任务。
        """
        self.task_manager.clear_new(id)

    def _load_tasks_from_yaml(self, section: str) -> list:
        """
        从 YAML 文件中加载老版任务。
        """
        try:
            with open(self.workday_tasks_yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get(section, [])
        except FileNotFoundError:
            print(f"YAML 文件未找到: {self.workday_tasks_yaml_path}")
            return []
        except yaml.YAMLError as e:
            print(f"解析 YAML 文件时出错: {e}")
            return []

    def _load_tasks_from_yaml_new(self, section: str, id: str) -> list:
        """
        从 YAML 文件中加载新版任务。
        """
        try:
            with open(self.workday_tasks_new_yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get(section, {}).get(id, [])
        except FileNotFoundError:
            print(f"YAML 文件未找到: {self.workday_tasks_new_yaml_path}")
            return []
        except yaml.YAMLError as e:
            print(f"解析 YAML 文件时出错: {e}")
            return []

    def _add_tasks_from_yaml(self, section: str, label: str = ""):
        """
        从 mock YAML 数据中添加老版任务到 TaskManager。
        """
        tasks = self._load_tasks_from_yaml(section)
        for task_info in tasks:
            self.task_manager.add_task(task_info["content"])
        print(f"已从 '{section}' 加载 {len(tasks)} 个老版任务。")

    def _add_tasks_from_yaml_new(self, section: str, label: str = "", id: str = None):
        """
        从 mock YAML 数据中添加新版任务到 TaskManager。
        """
        if id:
            tasks = self._load_tasks_from_yaml_new(section, id)
            for task_info in tasks:
                self.task_manager.add_task_new({"content": task_info["content"], "belong": id})
            print(f"已从 '{section}' 为 '{id}' 加载 {len(tasks)} 个新版任务。")
        else:
            print("未指定 id，无法加载新版任务。")

    def _morning_tasks(self):
        """
        加载清晨任务（老版）。
        """
        self._add_tasks_from_yaml("morning_tasks")

    def _morning_tasks_new(self, id: str):
        """
        加载清晨任务（新版）。
        """
        self._add_tasks_from_yaml_new("morning_tasks_new", id=id)

    def _start_work_tasks(self):
        # 示例方法，待实现
        print("开始工作任务...")

    def _finish_work_tasks(self):
        # 示例方法，待实现
        print("完成工作任务...")

    def _evening_tasks(self):
        # 示例方法，待实现
        print("晚间任务...")

    def _rest(self):
        # 示例方法，待实现
        print("休息...")

    def add_person_tasks(self, tasks: list):
        """
        添加个人任务（老版）。
        tasks 示例: ["任务1", "任务2"]
        """
        for task_name in tasks:
            self.task_manager.add_task(task_name)
        print(f"已添加 {len(tasks)} 个老版个人任务。")

    def add_person_tasks_new(self, tasks: list):
        """
        添加个人任务（新版）。
        tasks 示例: [{"content": "任务1", "belong": "user_a"}, {"content": "任务2", "belong": "user_a"}]
        """
        for task_info in tasks:
            self.task_manager.add_task_new(task_info)
        print(f"已添加 {len(tasks)} 个新版个人任务。")

    def get_current_task_info(self) -> dict:
        """
        获取当前老版任务信息。
        """
        task = self.task_manager.get_current_sequential_task()
        if task:
            return {"name": task.name, "status": task.get_status(), "prompt": task.request()}
        return {"message": "所有任务已完成！"}

    def get_current_task_info_new(self, id: str) -> dict:
        """
        获取指定 id 下当前新版任务信息。
        """
        task = self.task_manager.get_current_sequential_task_new(id)
        if task:
            return {"name": task.name, "belong": task.belong, "status": task.get_status(), "prompt": task.request()}
        return {"message": "所有任务已完成！"}

    def complete_current_task(self) -> dict:
        """
        完成当前老版任务。
        """
        task = self.task_manager.get_current_sequential_task()
        if task:
            task_name = task.name
            self.task_manager.complete_current_task()
            next_task = self.task_manager.get_current_sequential_task()
            if next_task:
                return {"message": f"任务 '{task_name}' 状态更新为：{task.get_status()}\n---\n当前任务：{next_task.name} ({next_task.get_status()})\n提示: {next_task.request()}"}
            else:
                return {"message": f"任务 '{task_name}' 状态更新为：{task.get_status()}\n---\n所有任务已完成！"}
        return {"message": "没有待完成的任务。"}

    def complete_current_task_new(self, id: str) -> dict:
        """
        完成指定 id 下当前新版任务。
        """
        task = self.task_manager.get_current_sequential_task_new(id)
        if task:
            task_name = task.name
            self.task_manager.complete_current_task_new(id)
            next_task = self.task_manager.get_current_sequential_task_new(id)
            if next_task:
                return {"message": f"任务 '{task_name}' 状态更新为：{task.get_status()}\n---\n当前任务：{next_task.name} ({next_task.get_status()})\n提示: {next_task.request()}"}
            else:
                return {"message": f"任务 '{task_name}' 状态更新为：{task.get_status()}\n---\n所有任务已完成！"}
        return {"message": "没有待完成的任务。"}

    def get_all_tasks_status(self) -> list:
        """
        获取所有老版任务的状态。
        """
        return self.task_manager.get_task_list()

    def get_all_tasks_status_new(self, id: str) -> list:
        """
        获取指定 id 下所有新版任务的状态。
        """
        return self.task_manager.get_task_list_new(id)