# Taskerz 任务管理系统简易使用教程

## 1. 简介

Taskerz 是一个基于 Python 的任务管理系统，旨在帮助用户高效地管理日常任务。它由一个服务端（`taskerz`）和一个 macOS 客户端（`tasker_client_mac`）组成，支持任务的创建、更新、完成、查询，并集成了 macOS 本地自动化、Obsidian 看板和 Canvas 等功能。

## 2. 安装

在开始使用 Taskerz 之前，请确保您的系统已安装 Python 3.8+ 和 `uv` 包管理器。

1.  **克隆仓库**：
    ```bash
    git clone https://github.com/your-repo/taskerz.git
    cd taskerz
    ```

2.  **安装依赖**：
    ```bash
    uv pip install -r requirements.txt
    ```
    如果您是 macOS 用户，并且希望使用 `appscriptz` 提供的本地自动化功能，请确保您的系统已安装 `appscriptz` 依赖。如果遇到 `ModuleNotFoundError`，可以尝试：
    ```bash
    uv pip install appscriptz
    ```
    如果 `appscriptz` 无法安装或您不是 macOS 用户，系统将自动使用 mock 实现。

## 3. 服务端使用

服务端负责任务的存储、管理和调度。

### 3.1 启动服务端

在项目根目录下运行：

```bash
uv run src/taskerz/server.py
```
或者使用 `uvicorn`：
```bash
uvicorn src.taskerz.server:app --host 0.0.0.0 --port 8000
```

服务端默认运行在 `http://127.0.0.1:8000`。

### 3.2 任务配置

服务端通过 `workday_tasks.yaml` 和 `workday_tasks_new.yaml` 文件加载任务。这些文件应位于项目根目录。

**`workday_tasks.yaml` 示例：**

```yaml
morning_tasks:
  - content: "检查邮件"
    description: "处理所有新邮件"
    due_date: "今天"
    priority: "高"
  - content: "规划今日工作"
    description: "根据优先级安排任务"
    due_date: "今天"
    priority: "高"
```

**`workday_tasks_new.yaml` 示例：**

```yaml
daily_tasks:
  - name: "完成报告"
    description: "撰写并提交月度报告"
    due_date: "2024-12-31"
    priority: "高"
    belong: "工作"
  - name: "学习 Python"
    description: "完成在线课程第5章"
    due_date: "2024-12-20"
    priority: "中"
    belong: "个人发展"
```

### 3.3 服务端 API 接口 (FastAPI)

Taskerz 服务端提供了一系列 RESTful API 接口，用于任务的交互。以下是一些主要接口：

*   **`/receive` (GET)**: 获取当前待处理的任务信息。
*   **`/complete` (GET)**: 完成当前任务，并推进到下一个任务。
*   **`/update_tasks_new` (POST)**: 批量更新或添加新任务。
    *   请求体示例：`{"tasks": [{"name": "新任务", "description": "描述", "belong": "分类"}]}`
*   **`/list_tasks` (GET)**: 列出所有任务的状态。
*   **`/morning` (GET)**: 加载 `workday_tasks.yaml` 中的早晨任务。
*   **`/clear` (GET)**: 清空所有任务。

## 4. macOS 客户端使用

macOS 客户端负责与服务端交互，并执行本地自动化操作。

### 4.1 启动客户端

在项目根目录下运行：

```bash
uv run src/tasker_client_mac/server.py
```
或者使用 `uvicorn`：
```bash
uvicorn src.tasker_client_mac.server:app --host 0.0.0.0 --port 8001
```

客户端默认运行在 `http://127.0.0.1:8001`。

### 4.2 客户端主要功能

*   **任务处理 (`_deal_task`)**:
    *   **A! 任务**: 以 `A!{duration}{unit} {task_name}` 格式的任务（例如 `A!20M 休息` 或 `A!1P 专注工作`），会触发本地自动化（通过 `appscriptz` 运行 AppleScript/Shortcuts）。`M` 代表分钟，`P` 代表 Pomodoro（默认为 20 分钟）。
    *   **普通任务**: 弹出系统通知提醒。
*   **看板同步 (`kanban`, `add_kanban`)**:
    *   `kanban()`: 自动同步 Obsidian 看板中的任务到服务端。
    *   `add_kanban(priority)`: 手动同步指定优先级的看板任务。
*   **灵活任务池 (`build_flexible`)**:
    *   `build_flexible("任务内容", "flex", True)`: 添加灵活任务。
    *   `build_flexible("池名称", "pool", True)`: 从指定池中构建任务。
*   **Canvas 提示 (`tips`)**:
    *   `tips("category:proj:ques:detail")`: 在本地 Obsidian Canvas 文件中添加带分类和颜色的提示/备注。
*   **任务生命周期管理**:
    *   `query_the_current_task()`: 查询当前任务。
    *   `start()`: 启动当前任务，如果是 A! 任务则触发本地自动化。
    *   `close()`: 关闭当前任务，并同步到服务端。
    *   `run()`: 推进当前任务状态。

## 5. 示例工作流

以下是一个简单的 Taskerz 工作流示例：

1.  **启动服务端和客户端**：
    *   打开两个终端，分别运行服务端和客户端。

2.  **配置早晨任务**：
    *   编辑 `workday_tasks.yaml`，添加一些早晨任务。

3.  **加载早晨任务**：
    *   通过客户端 API 调用 `/morning` 接口（例如，使用 `requests` 库或浏览器访问 `http://127.0.0.1:8000/morning`）。

4.  **开始任务**：
    *   通过客户端 API 调用 `/start` 接口。如果当前任务是 A! 任务，客户端将执行本地自动化。

5.  **完成任务**：
    *   通过客户端 API 调用 `/close` 接口。任务状态将更新，并推进到下一个任务。

6.  **同步看板任务**：
    *   通过客户端 API 调用 `/build_kanban` 接口，将 Obsidian 看板中的任务同步到 Taskerz。

7.  **添加 Canvas 提示**：
    *   通过客户端 API 调用 `/tips` 接口，例如 `http://127.0.0.1:8001/tips?task=学习:Python:问题:如何使用FastAPI`。

通过这些步骤，您可以开始使用 Taskerz 管理您的日常任务。