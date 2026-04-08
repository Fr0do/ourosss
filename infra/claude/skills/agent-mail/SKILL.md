---
name: agent-mail
description: Interact with MCP Agent Mail — send/receive messages between agents, manage file reservations (leases), register identities. Use when coordinating multiple agents, checking inbox, sending inter-agent messages, or managing file leases.
allowed-tools: mcp__mcp_agent_mail__*
---

# Agent Mail

MCP Agent Mail сервер установлен. Используй инструменты для координации агентов.

## Типичный воркфлоу

### Старт сессии
```
macro_start_session(project_key=<абс.путь>, ...)
```
Или по шагам:
1. `ensure_project(human_key=<абс.путь>)` — получить project_key
2. `register_agent(project_key, program="claude-code", model="claude-sonnet-4-6", task_description=...)` — зарегистрировать себя

### Отправить сообщение
```
send_message(project_key, sender_name, to=[...], subject, body)
```

### Прочитать входящие
```
fetch_inbox(project_key, agent_name)
```

### Зарезервировать файлы перед правками
```
file_reservation_paths(project_key, agent_name, paths=[...], ttl_seconds=3600, exclusive=true, reason="...")
```
После завершения: `release_file_reservations(project_key, agent_name)`

### Ответить в тред
```
reply_message(project_key, sender_name, thread_id, body)
```

## Ключевые инструменты

| Инструмент | Назначение |
|---|---|
| `macro_start_session` | Старт: проект + агент одним вызовом |
| `register_agent` | Регистрация identity агента |
| `send_message` | Отправить сообщение |
| `fetch_inbox` | Входящие |
| `acknowledge_message` | Подтвердить прочтение |
| `reply_message` | Ответ в тред |
| `search_messages` | Поиск по FTS |
| `summarize_thread` | Резюме треда |
| `file_reservation_paths` | Занять файлы (lease) |
| `release_file_reservations` | Освободить файлы |
| `list_file_reservations` | Активные leases |
| `list_agents` | Агенты в проекте |
| `whois` | Профиль агента |
| `doctor check` | Диагностика mailbox |

## Web UI
После запуска сервера: открой `/mail` в браузере — unified inbox всех проектов.
Human Overseer compose: `/mail/{project}/overseer/compose`

## Частые ошибки
- **"from_agent not registered"** → сначала `register_agent` с правильным `project_key`
- **Конфликт lease** → `file_reservation_paths` вернёт список конфликтов; договорись через `send_message` или жди истечения TTL
