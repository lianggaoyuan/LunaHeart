# Luna Heart 开发基础

当前只实现本地单用户聊天、会话切换、历史记录与模拟多轮回复。默认不连接任何外部模型，不需要密钥。请使用虚构测试信息。

## 启动

要求 Python 3.11+，Node.js 20.19+ 或 22.12+。

在 `code/backend` 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

在另一个终端的 `code/frontend` 中执行：

```powershell
npm ci
npm run dev
```

访问 http://127.0.0.1:5173 ，接口文档为 http://127.0.0.1:8000/docs 。前端开发代理将 `/api` 转发到后端，部署时需要单独配置反向代理。

可设置环境变量 `LUNA_DATABASE_PATH`（SQLite 路径）、`LUNA_ALLOWED_ORIGINS`（逗号分隔的前端地址）。前端 `VITE_API_BASE_URL` 默认 `/api/v1`。当前不自动读取 `.env`，请通过终端或运行配置传入。

## 目录和职责

```text
backend/app/
  main.py          组装依赖与生命周期
  api.py           HTTP 路由，不放模型和数据库细节
  schemas.py       对外请求与响应校验
  service.py       聊天业务编排
  repository.py    数据读写与原子事务
  domain.py        内部数据类型与模块接口
  agent.py         上下文、检索、模型适配器
  config.py        环境配置
frontend/src/
  api.ts           唯一 HTTP 调用入口
  types.ts         API 类型
  composables/     会话状态与交互流程
  components/      可复用展示组件
  App.vue          页面组装
```

## 后续模块接入

1. 真实模型：实现 `ModelProvider.generate`，在 `create_app` 中注入。适配器内部处理密钥、超时与供应商协议。接入时同步修改响应的 provider 标识，不要继续显示 mock。
2. RAG：实现 `KnowledgeRetriever.search`。现在默认返回空结果；有专业审核知识后再接入。实际引用关联需要扩展生成结果、后端 Schema 与前端类型，不能直接把全部检索结果当作回答引用。
3. 档案与状态：实现 `ContextSource.build`，读取经授权的数据。之后可增加用户作用域参数，不把用户状态直接由前端拼到系统提示中。
4. 日记、状态触发：按独立业务模块新增 schemas、路由、服务和存储；触发服务复用 AgentService，不在聊天路由里加入定时判断。
5. 长期记忆：单独负责候选提炼、审核写入、来源关联和过期删除；不要把所有历史对话无限塞入上下文。当前只传最近 20 条消息。

这些接口是明确的扩展位置，不代表对应功能已经实现。当前没有登录、知识审核、医疗回答校验或危机干预功能，不能直接用于真实用户服务。未来多人模式必须在后端引入鉴权，并给所有存储查询增加用户归属校验。

## 接口约定

- `GET /api/v1/health`：服务状态与模拟模式。
- `POST /api/v1/conversations`：新建会话。
- `GET /api/v1/conversations`：最多最近 100 个会话。
- `GET /api/v1/conversations/{id}/messages`：会话历史。
- `POST /api/v1/conversations/{id}/messages`：传入 UUID 类型的 `client_message_id` 和 1—4000 字 `message`。

相同会话与请求标识重复提交不会重复落库；同一标识用于不同内容返回 409。模型失败时不保存半轮消息。不同请求同时基于旧历史生成时，较晚提交返回 409，避免保存前后矛盾的历史。取消前端重试不能取消已经完成的服务端写入，需重新加载历史核对。

列表目前未分页，适合本地小规模开发。扩展多人使用前增加历史分页、模型 token 预算与服务端请求限流。SQLite schema 使用 `user_version=1`；任何结构变更都应增加显式迁移，不能只修改建表语句。

## 检查

后端在 `backend` 下：`python -m pytest`。前端在 `frontend` 下：`npm run build`。

修改规则：路由只做输入输出转换；SQL 只放存储层；模型协议只放适配器；组件不直接请求 HTTP。新增 API 同时更新 OpenAPI、前端类型与 README。错误展示给用户可读文案，不记录完整敏感对话或凭据。
