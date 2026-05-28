# AGENTS.md

## 常见错误处理

### 终端与编码

- PowerShell 默认输出曾把 UTF-8 中文显示成乱码，但文件本身是正常 UTF-8。
- 遇到中文显示异常时，先用 `Get-Content -Encoding utf8` 或 Node 按 UTF-8 读取确认，不要直接判断源码损坏。

### uv 缓存

- `uv add tzdata` 首次失败，原因是默认 uv 缓存路径初始化异常。
- 临时设置 `UV_CACHE_DIR=D:\grade-manager\.uv-cache` 后完成了依赖安装，但后续复用该临时缓存时又出现权限问题。
- 依赖安装完成后，后端测试可直接回到默认 `uv run pytest ...` 执行。

### Windows 手动启动

在当前 Codex 沙箱 PowerShell 里，`Start-Process` 曾因环境表存在重复 `Path/PATH` 报 `已添加项。字典中的关键字:“Path”所添加的关键字:“PATH”`。需要后台稳定运行时，使用提升权限后的 `Start-Process`，或在用户自己的 PowerShell 窗口直接启动。

- `cmd start /b` 可短暂拉起进程，但从工具会话启动时可能随父进程结束而退出，不适合作为稳定后台启动方式。

### Git 提交与推送

- 沙箱内 `git add -u` 曾因无法创建 `.git/index.lock` 报 `Permission denied`；需要提升权限后再暂存。
- `git commit` 首次失败，因为本仓库没有配置 `user.name` 和 `user.email`。
- 最近提交作者为 `stucc <student_cc@qq.com>`，本次只设置了仓库本地 Git 配置，未改全局配置。
- `git push origin main` 第一次 SSH 握手失败，报 `kex_exchange_identification ... connection abort`；重试后成功。

## 启动与测试命令

Windows前端启动：`$env:VITE_API_BASE_URL='http://127.0.0.1:8000/api/v1'; npm run dev -- --host 127.0.0.1 --port 3000`。

后端启动： `uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

- 后端：`uv run pytest -v`
- 前端：`npm run test`
- 前端：`npm run build`
- 前端：`npm run lint`
