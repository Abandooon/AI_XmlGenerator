docker rm -f vllm-audit-debug >/dev/null 2>&1; docker run --gpus all -it -p 8000:8000 -e VLLM_STRUCTURED_OUTPUT_AUDIT=true -e VLLM_AUDIT_PERSIST=true -e VLLM_AUDIT_LOG_DIR=/audit-logs -e VLLM_AUDIT_RECORD_ALLOWED_TOKENS=false -e VLLM_AUDIT_IN_RESPONSE=false -v $HOME/audit-logs:/audit-logs --name vllm-audit-debug vllm-audit:stable-final --host 0.0.0.0 --port 8000 --model deepseek-ai/DeepSeek-R1-Distill-Qwen-32B --tensor-parallel-size 4 --gpu-memory-utilization 0.85 --max-model-len 40000


下面这份就是你可以直接当 README / 移交流程文档用的“审计版 vLLM”项目说明。它包含：

* 项目背景与目标
* 我们到底对 vLLM 改了哪些代码
* 最终系统是怎么运作的（多进程＋落盘＋管理 API）
* 目录/环境变量/接口
* 以后怎么启服务、怎么在新机器还原
* 一行版检查命令

我会在关键技术点后面加引用，标记这是直接来自你现在的实现代码，比如审计 tracker 如何持久化、如何从环境变量初始化这些逻辑等。 

---

## 1. 项目背景

我们在使用 vLLM 的 Structured Outputs（基于 JSON Schema / 语法约束解码）做合规型/结构化响应。但业务上有两个更高的诉求：

1. **可解释性 / 合规取证**
   监管/QA 不想只看到“最终 JSON”，他们想问：

   * 模型在生成每个 token 时是否被约束？
   * 哪些 token 被拒绝？有没有反复回滚？
   * 哪个状态机分支被选中？
     这些是“为什么它会这样回答？”的证据。

2. **现场排障**
   线上 Structured Output 有时候会卡住，比如 grammar 太严、不断回滚、或状态跳转异常。我们要能复盘“它卡在哪一步”。

原生 vLLM 没有把这些细节暴露出来，更没有一个可查询 / 可导出的轨迹系统。所以我们自己加了一个**“审计追踪系统”**，让每次结构化输出的生成过程都可追溯。这个系统提供逐 token 的事件时间线（bitmask 限制、state_transition、rollback、finalize 等），并且可以通过内部管理 API 拉出来查看。

---

## 2. 项目目标（你现在已经实现了的）

### 2.1 最终目标

* **按 request_id 记录一整条“生成轨迹 (trail)”**
  每个用户请求有一个唯一 `request_id`，我们把它透传到 Structured Output 解码层，作为这条 trail 的主键。

* **实时记录解码过程的关键事件**
  包括 state 切换、允许 token 的约束情况（允许 token 的数量，而不是整张 bitmask，以免过大）、token 接受、回滚、终止等。

* **运行时可开关**
  是否开启审计、是否持久化、是否记录 allowed_tokens 明细，全部由环境变量控制，而不是硬编码。

* **不污染模型响应**
  正常 `/v1/chat/completions` 响应仍是 OpenAI 格式，不带审计信息（我们保持 `VLLM_AUDIT_IN_RESPONSE=false` 语义）。

* **Start → Event → Finalize 全流程落盘**
  Trail 不是只放内存，而是落到共享卷 `/audit-logs/audit.ndjson`，写成 NDJSON（每行一条事件）。EngineCore 写、APIServer 读，同一份卷，跨进程就能共享。

* **用内部管理 API 拉取 / 导出**
  我们新增 `/v1/admin/audit/*` 一套只给后端/合规/运维的人用的接口，而不是暴露给普通用户。

### 2.2 为什么“落盘”是必须的

vLLM 在推理时有两个进程角色：

* **EngineCore**：负责真正的推理、约束解码（Structured Output / xgrammar 等）。
* **APIServer**：FastAPI/OpenAI 兼容服务，提供 HTTP 路由（包括我们的审计接口）。

这两个进程各自 import 了一份 `StructuredOutputAuditTracker` 单例 `_global_audit_tracker`。也就是说，**它们不共享内存**，所以“EngineCore 写审计事件、APIServer 读审计事件”不起作用，除非我们做跨进程存储。

我们的方案 A 是：让 EngineCore 在生成时把轨迹 append 成 NDJSON 到 `/audit-logs/audit.ndjson`，然后 APIServer 的审计 API 去扫这个文件并聚合，再返回 `/v1/admin/audit/list`、`/trail/{id}` 等。这就是你刚刚已经跑通的模式。

---

## 3. 架构总览（现状版）

### 3.1 关键对象：StructuredOutputAuditTracker

我们引入了一个全局审计 tracker：

```python
class StructuredOutputAuditTracker:
    # 持有所有 trail (request_id -> AuditTrail)
    # 同时知道：
    #   enabled (是否开启审计)
    #   persist_to_disk (是否落盘)
    #   log_dir (/audit-logs)
    #   _ndjson_path (/audit-logs/audit.ndjson)
    #   pid/hostname 用于多进程标记
```

tracker 做的事情：

1. **start_trail(request_id, backend_type, grammar_spec)**

   * 初始化该请求的 trail；
   * 把 `start_time`、`backend_type` 写入内存；
   * 立刻 `_persist_line("start_trail", {...})` 写一条 NDJSON 记录到 `/audit-logs/audit.ndjson`。
     这样 APIServer 能知道这条请求存在。

2. **record_event(request_id, event_type=...)**

   * 每一步解码（比如状态切换、允许 token 更新、回滚等）都会调用；
   * 事件会被追加到该 trail 的 `events[]`；
   * 同时 `_persist_line("event", {"request_id":..., "event": event.to_dict()})` 写到 NDJSON。

3. **finalize_trail(request_id)**

   * Trail 结束时（推理完成），我们调用 `AuditTrail.finalize()`，它会给 trail 写上 `end_time = time.time()`。
   * 然后 `_persist_line("finalize", {"request_id":..., "summary": trail.to_dict(include_events=False)})` 再落一行 NDJSON，含 `end_time`、`duration`、统计信息（比如总 token 数、回滚次数等）。
   * 这样 APIServer 再去扫 NDJSON，就能填上 `end_time` 和 `duration`，而不是 null。

Tracker 在初始化时会根据环境变量检查：

* 审计是否开启 (`VLLM_STRUCTURED_OUTPUT_AUDIT`)
* 是否要落盘 (`VLLM_AUDIT_PERSIST`)
* 落盘目录是什么 (`VLLM_AUDIT_LOG_DIR`)
* 是否记录 allowed_tokens 明细 (`VLLM_AUDIT_RECORD_ALLOWED_TOKENS`)
  这些值通过 `get_audit_tracker()` 读取并注入到 `StructuredOutputAuditTracker(...)` 的构造里。

### 3.2 EngineCore 侧逻辑（写入）

* Structured Output 的解码后端（`backend_xgrammar.py`, `backend_outlines.py`, `backend_guidance.py`, `backend_lm_format_enforcer.py`）在第一次真正处理该请求时会：

  * 绑定 `request_id`
  * 调用 `audit_tracker.start_trail(...)`
  * 后续在 token 级别/状态机级别的循环内调用 `audit_tracker.record_event(...)`
  * 推理结束后调用 `audit_tracker.finalize_trail(...)`

这些文件都在 `vllm/v1/structured_output/`，我们已经把打点逻辑加进去了。

### 3.3 APIServer 侧逻辑（读取）

我们新增了 `audit_admin_api.py`（FastAPI Router），并在主 `api_server.py` 里用：

```python
from vllm.v1.structured_output.audit_admin_api import router as audit_router
app.include_router(audit_router, prefix="/v1/admin/audit")
```

让 APIServer 暴露 `/v1/admin/audit/*`。这个 Router 做两件事：

1. **扫磁盘（/audit-logs/audit.ndjson）**
   它实现了 `_load_persisted_trails()` / `_merge_memory_and_disk()`：

   * `_load_persisted_trails()`：读取 NDJSON，每行都带 `record_type`（`start_trail` / `event` / `finalize`），按 `request_id` 聚合，拼出一份 trail 视图。
   * `_merge_memory_and_disk()`：把这份 trail 视图和 APIServer 进程内存里的 tracker 合并（APIServer 自己也可能正在处理一些请求），得到“全局视图”。

2. **对外提供管理 API**

   * `GET /v1/admin/audit/list?limit=N`：返回最近 N 条 trail 的摘要（包括 `total_steps`, `total_tokens_generated`, `rollbacks`, `errors`, `start_time`, `end_time` 等）。
   * `GET /v1/admin/audit/trail/{request_id}`：返回该 request_id 的全部事件时间线（包括 `bitmask_update`, `state_transition`, `rollback` 等逐步记录）。
   * `GET /v1/admin/audit/stats`：基于合并视图计算全局统计（活跃 trail 数、平均步数、平均时长等）。
   * 还有 `export`、`clear`、`delete` 等管理动作。

结果就是：
EngineCore 写 NDJSON，APIServer 扫 NDJSON 重建 trail → 现在 `/v1/admin/audit/list` 已经能看到我们刚刚的 `chatcmpl-...`，`/trail/<id>` 还能看到 60+ 个逐步事件，这是我们验证成功的现状。

---

## 4. 我们对 vLLM 本体做的修改清单

这部分是代码级别/补丁级别，后面交接给别人时最有用。

### 4.1 结构化请求对象：request_id 透传

文件：`vllm/v1/request.py`（我们本地叫 `request_v1.py` 再覆盖）

* 在把上游请求组装成 Structured Output 请求 (`StructuredOutputRequest`) 时，**必须把 `request_id` 一起传下去**，而不是只传 `sampling_params`。
* 正确逻辑类似：

  ```python
  structured_output_request = StructuredOutputRequest(
      sampling_params=request.sampling_params,
      request_id=request.request_id,
  ) if request.sampling_params else None
  ```

  如果没透传，后面审计系统根本不知道这个推理是哪条 request，轨迹就无法按 request_id 归档。

### 4.2 各 Structured Output backend 的打点

文件：

* `backend_xgrammar.py`
* `backend_outlines.py`
* `backend_guidance.py`
* `backend_lm_format_enforcer.py`

这些后端（也就是不同 grammar/constraint 解码器）我们都加了类似逻辑：

* 第一次遇到这个请求时：

  * 记录 `self._request_id = request_id`
  * 调 `audit_tracker.start_trail(request_id, backend_type=..., grammar_spec=...)`
* 在 token 循环里：

  * 对每一步状态/约束/回滚调用 `audit_tracker.record_event(...)`
* 在解码结束时：

  * 调 `audit_tracker.finalize_trail(request_id)`，这样会写出 `finalize` 行，带 `end_time`。

### 4.3 审计追踪核心：audit_tracker.py

主要变化：

1. 新增 `StructuredOutputAuditTracker` 并作为全局单例 `_global_audit_tracker`。
2. 支持环境变量控制是否启用审计、是否落盘、审计目录位置等。
3. 在 `start_trail()` / `record_event()` / `finalize_trail()` 里调用 `_persist_line()`，把 trail 的起点、每个事件、最后的总结（含 end_time/duration）写成 NDJSON，统一放在 `/audit-logs/audit.ndjson`。
4. `finalize_trail()` 里我们加了 `trail.finalize()`（设置 `end_time = time.time()`）并落 `"record_type": "finalize"` 的总结行，所以现在 list/trail API 能看到 `duration` 等信息，而不是永远 null。

### 4.4 持久化相关（NDJSON）

我们扩展 tracker 的 `__init__` 让它接收：

* `persist_to_disk` (bool)
* `log_dir` (比如 `/audit-logs`)
  并准备 `_ndjson_path = os.path.join(log_dir, "audit.ndjson")`，后续 `_persist_line(...)` 全部往这一个文件 `append`。

### 4.5 审计管理 API：audit_admin_api.py

我们新增了 FastAPI 的 `router`，包含：

* `/health`
* `/list`
* `/trail/{request_id}`
* `/stats`
* `/export`
* `/clear`
* `/trail/{request_id}` (DELETE)
  这些接口内部先从磁盘扫描 `/audit-logs/audit.ndjson`，聚合 trail，再返回给调用方。

### 4.6 OpenAI入口：api_server.py

我们把 `audit_admin_api.router` 注册到了主 app：

```python
from vllm.v1.structured_output.audit_admin_api import router as audit_router
app.include_router(audit_router, prefix="/v1/admin/audit")
```

注意：`prefix` 必须是字符串字面量，否则会 SyntaxError，服务直接起不来（我们踩过）。

---

## 5. 目录结构 / 文件位置

### 容器内（运行时）

* Structured Output + 审计：
  `/usr/local/lib/python3.12/dist-packages/vllm/v1/structured_output/`

  * `backend_xgrammar.py`
  * `backend_outlines.py`
  * `backend_guidance.py`
  * `backend_lm_format_enforcer.py`
  * `backend_types.py`
  * `request.py`（StructuredOutputRequest）
  * `audit_tracker.py`
  * `audit_integration.py`
  * `audit_admin_api.py`

* vLLM v1 请求入口：
  `/usr/local/lib/python3.12/dist-packages/vllm/v1/request.py`
  （来自我们本地的 `request_v1.py`，负责 request_id 透传）

* FastAPI 入口：
  `/usr/local/lib/python3.12/dist-packages/vllm/entrypoints/openai/api_server.py`
  （挂载审计路由）

### 本地补丁目录（开发者维护）

宿主机：`~/fixed`
你用 WinSCP 把这些文件放到 `~/fixed`，然后用 `install.sh` 批量 `docker cp` 进容器并 `compileall` 强制刷新 `.pyc`，避免老字节码覆盖新逻辑。

---

## 6. 运行时环境变量（必须传）

容器启动时我们现在要求带上这些（至少这些）：

```bash
-e VLLM_STRUCTURED_OUTPUT_AUDIT=true          # 打开审计
-e VLLM_AUDIT_PERSIST=true                    # 允许把审计事件落盘
-e VLLM_AUDIT_LOG_DIR=/audit-logs             # 挂载卷位置，EngineCore写+APIServer读
-e VLLM_AUDIT_RECORD_ALLOWED_TOKENS=false     # 不用记录完整allowed token表，只记数量，防止日志爆炸
-e VLLM_AUDIT_IN_RESPONSE=false               # 不把审计塞进模型响应，保持兼容
```

并且挂卷：

```bash
-v $HOME/audit-logs:/audit-logs
```

这样 EngineCore 会把 NDJSON 写到 `/audit-logs`（容器内路径），APIServer 也能看到同样的文件。

---

## 7. 对外管理 API（合规/排障用）

通过 `audit_admin_api.py` 注册到 `/v1/admin/audit/*`：

* `GET /v1/admin/audit/health`
  审计子系统健康状态（是否 enabled、trail 数、持久化目录可写等）

* `GET /v1/admin/audit/list?limit=N`
  最近 N 条请求的摘要，包括：

  * `request_id`
  * `backend_type`（比如 `"xgrammar"`)
  * `start_time` / `end_time`
  * `duration`
  * `total_steps`（事件步数）
  * `total_tokens_generated`
  * `total_rollbacks`
  * `total_errors`

* `GET /v1/admin/audit/trail/{request_id}`
  单条请求的完整轨迹，包含逐步事件列表（如 `bitmask_update`, `state_transition`, `rollback`），可以用于现场复盘。

* `GET /v1/admin/audit/stats`
  全局统计（活跃 trail 数、平均步长、平均时长等）。

* `POST /v1/admin/audit/export?format=ndjson`
  导出 NDJSON（合规/长期留痕用）。

* `POST /v1/admin/audit/clear`
  清空当前进程内存缓冲（危险操作，开发/调试场景用）。

* `DELETE /v1/admin/audit/trail/{request_id}`
  删除单条 trail（同样是高危，合规要谨慎）。

⚠️ 安全：
这条路由建议只在内网暴露或挂到受控反代后面，并带鉴权。不要直接开放给公网客户端。

---

## 8. 如何启动 / 重启 / 验证

你现在已经把容器 patch 好并 `docker commit` 成了一个镜像，这个镜像我们下面叫它：
`vllm-audit:stable-final`

我们要覆盖两个场景：

1. **同一台机器上重启（用现成固化镜像）**
2. **换一台机器重建（用 Dockerfile / build）**

### 8.1 同一台机器上重启（使用当前固化镜像）

假设：

* 你已经做过一次

  ```bash
  docker commit vllm-audit-test vllm-audit:stable-final
  ```
* 你要重新跑服务，容器名字还是用 `vllm-audit-test`。

**一行版启动命令：**

```bash
docker rm -f vllm-audit-test; docker run --rm -d --gpus all -p 8000:8000 -e VLLM_STRUCTURED_OUTPUT_AUDIT=true -e VLLM_AUDIT_PERSIST=true -e VLLM_AUDIT_LOG_DIR=/audit-logs -e VLLM_AUDIT_RECORD_ALLOWED_TOKENS=false -e VLLM_AUDIT_IN_RESPONSE=false -v $HOME/audit-logs:/audit-logs --name vllm-audit-test vllm-audit:stable-final python3 -m vllm.entrypoints.openai.api_server --host 0.0.0.0 --port 8000 --model Qwen/Qwen2.5-0.5B-Instruct
```

解释一下这个容器：

* 镜像是我们固定下来的 `vllm-audit:stable-final`（也就是打过补丁的 vLLM）
* 容器内会带上所有我们需要的审计环境变量、并且把宿主机的 `$HOME/audit-logs` 挂到容器内 `/audit-logs`

### 8.2 新机器还原（重新 build 的版本）

如果你把所有补丁文件（那些在 `~/fixed` 里的版本）和一个简单的 Dockerfile 一起带到了新机器，你可以直接 build 成全新镜像，不用先跑原生 vLLM 再 `docker cp`。

你准备的 Dockerfile 里要做的事是：

1. `FROM` 原始 vLLM GPU 基础镜像
2. `COPY` 我们修改过的所有文件到容器 `dist-packages/vllm/...`
3. `RUN python3 -c "import compileall; compileall.compile_dir(..., force=True)"`

然后在新机器上一行 build + run 就可以了：

```bash
docker build -t vllm-audit:stable-final . && docker run --rm -d --gpus all -p 8000:8000 -e VLLM_STRUCTURED_OUTPUT_AUDIT=true -e VLLM_AUDIT_PERSIST=true -e VLLM_AUDIT_LOG_DIR=/audit-logs -e VLLM_AUDIT_RECORD_ALLOWED_TOKENS=false -e VLLM_AUDIT_IN_RESPONSE=false -v $HOME/audit-logs:/audit-logs --name vllm-audit-test vllm-audit:stable-final python3 -m vllm.entrypoints.openai.api_server --host 0.0.0.0 --port 8000 --model Qwen/Qwen2.5-0.5B-Instruct
```

差别就是这里用了 `docker build` 而不是 `docker commit`，更适合标准化分发。

---

## 9. 一行版状态检查（健康+模型+审计）

启动完容器后，你可以用下面这一行来做冒烟自检：

```bash
curl -sS -H 'Content-Type: application/json' -d '{"model":"Qwen/Qwen2.5-0.5B-Instruct","messages":[{"role":"user","content":"Return a JSON with user_name (string) and confidence (number). Use a realistic value."}],"response_format":{"type":"json_schema","json_schema":{"name":"demo_schema","schema":{"type":"object","properties":{"user_name":{"type":"string"},"confidence":{"type":"number"}},"required":["user_name","confidence"],"additionalProperties":false}}},"max_tokens":64}' http://localhost:8000/v1/chat/completions | tee /tmp/resp.json && RID=$(jq -r '.id' /tmp/resp.json); echo "RID=$RID"; docker exec vllm-audit-test bash -lc 'ls -lh /audit-logs && tail -n 10 /audit-logs/audit.ndjson'; curl -sS "http://localhost:8000/v1/admin/audit/list?limit=5" | jq .; curl -sS "http://localhost:8000/v1/admin/audit/trail/$RID" | jq .
```

这个做了 4 件事连在一起：

1. 打一条结构化输出请求，强制触发 xgrammar 约束解码 → 触发审计记录。
2. 保存响应到 `/tmp/resp.json`，并把 `.id`（也就是 request_id）提出来放到 `RID`。
3. 在容器里看 `/audit-logs/audit.ndjson` 是否追加了 `start_trail` / `event` / `finalize` 行。
4. 调你的审计管理 API：

   * `/v1/admin/audit/list` → 确认 trail 出现
   * `/v1/admin/audit/trail/$RID` → 确认逐步事件时间线可取回

如果这一步跑通，说明：

* 审计开关启了
* NDJSON 正在写
* APIServer 能从 NDJSON 合成全局视图
* request_id 透传是好的
* 你的路由 `/v1/admin/audit/*` 已成功挂到主 FastAPI app 上

也就是：整条“合规追踪链路”是健康的 ✅

---

## 10. TL;DR 给未来接手的人看的三句话总结

1. 这个镜像是“带审计追踪的 vLLM Structured Outputs”。它会在推理时记录逐 token 的约束解码过程，并持久化为 NDJSON，后端可以通过 `/v1/admin/audit/*` 回放整条轨迹，包含状态转移、允许候选 token 数、最终定稿和 finalize（含 end_time/duration）。

2. 最核心的改动点有三个：

   * `request_id` 透传到 StructuredOutputRequest（`vllm/v1/request.py`）
   * 各 grammar backend 在首次绑定、每步解码和结束时打点到 `StructuredOutputAuditTracker`
   * `audit_tracker.py` 支持 `_persist_line()`，把 trail 以 NDJSON 落到 `/audit-logs/audit.ndjson`，APIServer 通过 `audit_admin_api.py` 扫这个文件并聚合结果。 

3. 使用时一定要带上这些环境变量并挂盘：

   ```bash
   -e VLLM_STRUCTURED_OUTPUT_AUDIT=true \
   -e VLLM_AUDIT_PERSIST=true \
   -e VLLM_AUDIT_LOG_DIR=/audit-logs \
   -e VLLM_AUDIT_RECORD_ALLOWED_TOKENS=false \
   -e VLLM_AUDIT_IN_RESPONSE=false \
   -v $HOME/audit-logs:/audit-logs
   ```

   否则 APIServer 看不到 EngineCore 写下的轨迹，`/v1/admin/audit/list` 会是空。



----------------------------------------------------------------------------------------------------------------------------------------------------------------
\textbf{RQ1.} 在单文件 AUTOSAR ARXML 生成任务中，不同程度的知识注入与 Layer-1 生成期约束会如何影响生成正确性、审计可得性与开销成本？

\paragraph{实验目标.}
RQ1 聚焦于受控环境：单组件、单 ARXML 文件的生成，而非系统级多文件装配。目标是回答三个问题：
(1) 在没有跨文件依赖的前提下，框架是否可以通过 Layer-1 约束实现 100% 结构正确性；
(2) 审计轨迹 $\tau$ 与结构性证据 $\pi_{\text{struct}}$ 是否可以在推理过程中稳定产出，从而形成可独立重验的复合证据 $\Pi$；
(3) 这些保证需要付出多少推理时延与算力开销。

\paragraph{模型与数据集.}
所有实验均使用同一推理后端：vLLM 部署的 DeepSeek-R1-Distill-Qwen-32B 模型，以消除模型差异带来的干扰。测试集包含 60 个代表性 AUTOSAR 单组件案例。每个案例运行 3 次，使用固定随机种子 $42$, $1001$, $20250701$，共计 180 次试验，以估计方差并避免偶然“走运”的单次成功。

\paragraph{策略对比.}
我们比较四个策略，形成一条从「无约束、无知识」到「有知识且受 Layer-1 约束」的演进链。为便于后续分析，我们将它们记为 S0--S3。

\begin{itemize}
\item \textbf{S0: vLLM} \quad
仅调用本地 vLLM，直接请求生成目标 ARXML，不注入任何领域知识，不施加任何生成时约束。S0 作为最弱下界，反映“纯大模型自由生成”的自然状态。

```
\item \textbf{S1: vLLM + RAG} \quad
在 S0 的基础上，向大模型注入由知识图谱 (KG) / 规范片段检索得到的上下文（RAG）。此策略对应工业界普遍的“加上下文就更可靠”的直觉：模型可以在提示中看到 AUTOSAR 片段、接口定义、字段说明等。然而，S1 仍然没有生成期约束；因此它往往“自信而不受约束”，可能输出在语义上看似合理的片段，但在结构上仍然是无效或不可解析的 XML。

\item \textbf{S2: vLLM + RAG + JSON Schema} \quad
在 S1 的基础上，引入 Layer-1 约束。具体做法是先要求大模型生成一个受 JSON Schema 约束的中间结构（例如组件描述的层级化 JSON），Schema 明确哪些字段是必填、字段类型范围、允许的枚举、出现次数等；之后再将该结构投影/转换为 AUTOSAR ARXML。换言之，S2 在推理时通过 Schema 约束\emph{中间表示}的合法性，并将“合法中间表示 $\rightarrow$ 合法 ARXML”视为一个程序化、可验证的模型转换步骤。JSON Schema 的优点是：它允许我们对必备字段进行强制，却仍给模型在字段内容上的自由度；同时，这个自由度往往鼓励模型“填满”语义上合理的细节。

\item \textbf{S3: vLLM + RAG + GBNF} \quad
同样引入 Layer-1 约束，但不再经由 JSON Schema 中间层，而是直接以 GBNF / 有限状态自动机 (DFA) 形式描述可接受的 ARXML 文法，并要求大模型仅在该文法允许的前缀集合内进行受限解码（prefix-safe generation）。从理论上看，S3 是最贴近 AUTOSAR ARXML 语法本身的约束形式：我们用 GBNF 对标签嵌套、顺序、出现次数等进行精确刻画，并在生成时拒绝一切不合法前缀。

\smallskip
然而，我们在实践中观察到一个重要现象：在强 GBNF 约束下，大模型倾向于走“最短合法路径”，即只输出满足文法的最小骨架，而不主动补充丰富的子结构。为避免这种“最短合格输出”倾向，S3 需要我们在文法中\emph{显式声明必须展开的标签与段落}，例如强制要求特定子元素必须出现至少一次、并在固定顺序下完整给出。这种做法可以显著提高结构完备度，但也进一步收紧了模型的自由度，把更多设计决策硬编码进文法本身。
```

\end{itemize}

需要强调的是：S2 与 S3 在框架层面都体现为 Layer-1 生成期约束（L1）。两者的差异不是“强约束 vs 弱约束”，而是“约束接口的形态”：
\begin{itemize}
\item S2 通过 JSON Schema 约束一个中间的、类对象的结构，然后再进行确定性的结构化投影到 XML；
\item S3 通过 GBNF / DFA 直接约束最终 ARXML 的文法。
\end{itemize}
这两种实现为我们提供了一个工程向的观察窗口：当约束直接贴在最终语法层（S3）时，我们得到的是结构绝对正确、但内容可能极简；当约束贴在较语义化的中间对象层（S2）时，我们往往得到的是更“丰满”的实例，但需要额外的一步稳定的 JSON$\rightarrow$XML 转换。

\paragraph{测量指标.}
为回答 RQ1 的三大问题（正确性 / 审计性 / 成本），我们记录三类指标。

\textbf{(1) 正确性指标.}
我们对每次生成的 ARXML 计算三层合规率：
\begin{itemize}
\item \textit{结构合规 (Layer-1 Structural Compliance).}
生成结果必须通过 AUTOSAR 提供的 XSD 验证器。S2 与 S3 旨在通过生成期约束达到 100% 的结构合规率；S0 与 S1 预期会显著低于该水平（约 50% 左右）。
\item \textit{语义合规 (Layer-2 Semantic Compliance).}
我们将知识图谱 (KG) 中的约束（例如字段间依赖、取值域一致性等）和由 LLM 从自然语言规范抽取的约束统一编译为 SHACL 形态，对最终 ARXML 进行后验验证。该指标衡量的是局部语义一致性，而非跨文件全局一致性（后者在 RQ2 评估）。
\item \textit{逻辑合规 (Layer-2 Logic / SMT Compliance).}
对于可形式化为布尔/算术约束的局部逻辑（例如端口属性之间的相容性、区间范围满足性等），我们使用 SMT 求解器进行可满足性检查，记录是否存在冲突。该指标旨在捕捉“值与值之间”的约束违例。
\end{itemize}

\textbf{(2) 审计性指标.}
RQ1 的关键主张之一是：不仅要生成“正确”的工件，还要生成\emph{可证明其正确性来源}的工件。为此我们记录：
\begin{itemize}
\item \textit{审计轨迹完整率 (Audit Trail Completeness).}
我们对每次生成过程记录逐步审计轨迹
$\tau_t = \langle s_t, M_t, y_t, \delta(s_t, y_t), \Delta t \rangle$，
其中 $s_t$ 是生成状态机状态，$M_t$ 为当前约束上下文，$y_t$ 为生成片段，$\delta$ 为状态转移，$\Delta t$ 为时间戳。我们统计能够成功记录完整 ${\tau_t}*t$ 的试验比例。目标是该比例在 S2/S3 中达到 100%，证明 Layer-1 约束不仅约束输出，而且暴露了完整的状态机运行轨迹 $\rho$。
\item \textit{证据完备率 (Evidence Completeness).}
Layer-1 验证会产出结构性证据
$\pi*{\text{struct}} = \langle \rho, \text{cert}*{L1} \rangle$，
Layer-2 验证（SHACL/SMT）分别产出 $\pi*{\text{sem}}$ 与 $\pi_{\text{logic}}$。
我们将这些证据在一次生成会话后合成为
$\Pi = (\pi_{\text{struct}} \otimes \pi_{\text{sem}} \otimes \pi_{\text{logic}}) \oplus \tau$，
并封装成可验证产物包
$\psi = (a, \Pi, \phi)$。
我们统计能成功生成 $\Pi$ 并打包为 $\psi$ 的比例，作为“第三方可验证性”的代理指标：即该 ARXML 是否不仅结构正确，而且携带可以在独立验证器上重放的、机器可核查的证据。
\end{itemize}

\textbf{(3) 成本指标.}
为量化引入知识检索与 Layer-1 约束的代价，我们记录推理阶段的资源开销：
\begin{itemize}
\item \textit{生成时延 (Latency).}
从发出生成请求到得到最终 ARXML 的墙上时钟时间。对于 S2 和 S3，这一过程包括约束拒绝/回退（例如 DFA 拒绝无效前缀）或中间表示到 ARXML 的投影过程。
\item \textit{输入/输出 Token 开销.}
我们记录每次调用的输入 token 数与输出 token 数，以衡量 RAG 带来的 prompt 扩张（S1--S3 相对 S0）以及约束机制带来的生成停顿/回退（尤其在 S3 的 GBNF 约束下）。
\item \textit{审计文件体积.}
对于每次试验，我们持久化审计轨迹 ${\tau_t}*t$ 以及对应的 $\pi*{\text{struct}}$，并记录其字节大小与序列长度。这一指标体现了审计记录本身的存储/传输成本，也为后续 AGR（Audit-Guided Repair）提供可复现输入。
\end{itemize}

\paragraph{预期比较维度.}
RQ1 的结果分析将围绕以下三个维度展开：
(1) \textit{结构正确性 vs. 自由度.} 比较 S2 (JSON Schema) 与 S3 (GBNF) 在 XSD 合规率达到 100% 的同时，输出结构的“饱满度”是否不同；并讨论 S3 中“最短合法路径”倾向如何迫使我们在文法中手工指定必现标签，从而牺牲生成自由度。
(2) \textit{RAG 的真实贡献.} 对比 S0 与 S1，量化“仅靠上下文检索但无约束”是否真的改善语义/逻辑合规，还是主要带来更大的自信幻觉；这直接回应工业界对“RAG=可靠”的朴素假设。
(3) \textit{审计可得性与成本.} 比较 S2/S3 与 S0/S1 在审计轨迹完整率、证据完备率上的提升，同时衡量它们在生成时延、token 成本与审计文件体积上的额外开销。该比较为后续 AGR 提供依据：只有当 $\Pi$ 充分完整时，AGR 才能进行定点修复而非盲目重试。

\paragraph{小结.}
通过 S0--S3 的四策略对照，RQ1 并非仅验证“我们能不能生成看起来不错的 ARXML”，而是系统性地回答：
\emph{要想得到结构上 100% 合法、语义上可验证、并且携带可追责证据包 $\Pi$ 的产物，我们到底需要向生成管线中注入哪些机制（知识检索、Layer-1 约束、显式文法），以及这些机制各自的代价是什么。}
这为后续 AGR 的有界修复能力、以及 RQ2 中多文件场景下的可扩展性打下实验基础。
