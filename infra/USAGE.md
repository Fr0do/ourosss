# infra/ — памятка

Портативная инфра ourosss: hermes-конфиг, бот на сервере, авто-синк ноут ↔ сервер.

## TL;DR

| Хочу… | Команда |
|---|---|
| Засеять новый ноут | `bash infra/bootstrap.sh && hermes login` |
| Восстановить Claude скиллы на новом ноуте | `bash infra/local/restore-claude-skills.sh` |
| Засеять новый сервер | `ssh HOST 'mkdir -p ~/kurkin && cd ~/kurkin && git clone git@github.com:Fr0do/ourosss.git && bash ourosss/infra/server/bootstrap-server.sh'` |
| Засеять новый сервер c shared-user профилем | `ssh HOST 'mkdir -p ~/kurkin && cd ~/kurkin && git clone git@github.com:Fr0do/ourosss.git && OUROSSS_SHARED_USER=1 bash ourosss/infra/server/bootstrap-server.sh'` |
| Поднять pinned Python/uv на сервере | `~/kurkin/bin/ourosss-bootstrap-python` |
| Включить авто-синк на ноуте | `cp infra/local/com.ourosss.hermes-sync.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.ourosss.hermes-sync.plist` |
| Толкнуть всё на сервер прямо сейчас | `SERVER_HOST=kurkin-vllm bash infra/local/sync-push.sh` |
| Стянуть изменения на сервере прямо сейчас | `bash ~/kurkin/ourosss/infra/server/sync-pull.sh` |
| Перезапустить бота | `systemctl --user restart ourosss` |
| Перезапустить бота без systemd | `~/kurkin/bin/ourosss-run restart` |
| Логи бота | `journalctl --user -u ourosss -f` |
| Логи бота без systemd | `~/kurkin/bin/ourosss-run logs` |
| Логи синка (ноут) | `tail -f ~/Library/Logs/ourosss-sync.log` |
| Логи синка (сервер) | `tail -f ~/kurkin/logs/sync.log` |
| Проверить таймеры | `systemctl --user list-timers` |

## Архитектура одной картинкой

```
┌─────────────────── НОУТБУК (source of truth) ───────────────────┐
│  ~/.hermes/{config.yaml, memories/USER.md, .env, auth.json}     │
│  ~/.claude/skills/                                              │
│  ~/experiments/ourosss/.env                                     │
│         │                                                       │
│         │  launchd: каждые 30 мин                               │
│         │  infra/local/sync-push.sh                             │
│         ▼                                                       │
│  1. hermes skills snapshot export → infra/hermes/...            │
│  2. cp ~/.hermes/memories/USER.md → infra/hermes/memories/      │
│  3. rsync ~/.claude/skills → infra/claude/skills/               │
│  4. git commit + push если есть diff в infra/                   │
│  5. rsync ~/.hermes/.env, auth.json, ourosss/.env → server      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼ git push                  ▼ rsync ssh
        ┌──────────────┐           ┌──────────────────┐
        │ github.com   │           │ kurkin-vllm      │
        │ Fr0do/ourosss│           │ ~/kurkin/secrets/│
        └──────┬───────┘           └────────┬─────────┘
               │                            │
               │ git pull (systemd 15 мин)  │ симлинки
               ▼                            ▼
┌─────────────────── СЕРВЕР (kurkin-vllm) ────────────────────────┐
│  ~/kurkin/ourosss/         ← git checkout                       │
│  ~/kurkin/hermes/          ← ~/.hermes симлинк сюда             │
│  ~/kurkin/secrets/         ← .env, auth.json, hermes.env        │
│  ~/kurkin/logs/            ← логи бота + sync                   │
│                                                                 │
│  systemd --user units:                                          │
│    ourosss.service        ← бот, restart on failure             │
│    ourosss-sync.timer     ← каждые 15 мин дёргает sync-pull.sh  │
│      └─ sync-pull.sh:                                           │
│           git pull → если bot/ → uv sync + restart              │
│                    → если *.service → daemon-reload + restart   │
│                    → если skills-snapshot → hermes import       │
└─────────────────────────────────────────────────────────────────┘
```

## Принципы

1. **Source of truth = ноутбук.** Сервер только потребляет hermes-память/скиллы. Не редактировать `infra/hermes/memories/USER.md` на сервере вручную — следующий sync-pull затрёт.
2. **Секреты не в git, никогда.** Только через rsync (`infra/local/sync-push.sh` → `~/kurkin/secrets/`). В git живут только публичные конфиги.
3. **Симлинки, не копии.** Hermes хардкодит `~/.hermes` — поэтому на сервере он либо симлинкнут в `~/kurkin/hermes`, либо в shared-user режиме запускается с `HOME=~/kurkin/home`, где `~/.hermes` уже указывает в `~/kurkin/hermes`. Все файлы в `~/kurkin/secrets/` симлинкнуты туда, куда их ждут консьюмеры.
4. **Idempotency.** Bootstrap-скрипты можно перезапускать сколько угодно — они бэкапят существующие файлы и не ломают то что уже работает.
5. **Авто-синк не должен убивать таймер.** Все ошибки sync-pull/sync-push логируются и swallow'ятся, чтобы один кривой pull не остановил cron.

## Первичный деплой нового сервера — пошагово

```bash
# 1. На сервере
ssh kurkin-vllm
mkdir -p ~/kurkin && cd ~/kurkin
git clone git@github.com:Fr0do/ourosss.git
bash ourosss/infra/server/bootstrap-server.sh

# 2. Положить секреты (с ноута)
exit
SERVER_HOST=kurkin-vllm bash infra/local/sync-push.sh

# 3. На сервере: hermes auth + старт
ssh kurkin-vllm
hermes login                                    # один раз
systemctl --user enable --now ourosss
systemctl --user enable --now ourosss-sync.timer
sudo loginctl enable-linger $USER               # чтобы выживало без ssh-сессии

# 4. Проверка
systemctl --user status ourosss
journalctl --user -u ourosss -f
systemctl --user list-timers
```

## Частые операции

### Откатить бота к предыдущей версии
```bash
# На сервере
cd ~/kurkin/ourosss
git log --oneline -10
git reset --hard <hash>
systemctl --user restart ourosss
# Внимание: следующий sync-pull притянет main обратно. Для долгого rollback —
# создай ветку и поправь sync-pull.sh / останови таймер.
```

### Временно остановить авто-синк
```bash
# На ноуте
launchctl unload ~/Library/LaunchAgents/com.ourosss.hermes-sync.plist
# На сервере
systemctl --user stop ourosss-sync.timer
```

### Поменять hermes-конфиг
```bash
# На ноуте — редактируешь живой файл
vim ~/.hermes/config.yaml
# bootstrap.sh симлинкнул его на infra/hermes/config.yaml, так что edit
# попадает прямо в репо. Следующий launchd-цикл закоммитит и запушит.
# Если хочется немедленно:
bash infra/local/sync-push.sh
```

### Shared SSH user: изолировать Hermes и Claude под `~/kurkin`
```bash
# На сервере
cd ~/kurkin/ourosss
OUROSSS_SHARED_USER=1 bash infra/server/bootstrap-server.sh
~/kurkin/bin/ourosss-bootstrap-python

# После этого:
~/kurkin/bin/ourosss-profile hermes login
~/kurkin/bin/ourosss-claude
~/kurkin/bin/ourosss-run start
```

`ourosss-profile` запускает команду с `HOME=~/kurkin/home`, так что Hermes читает `~/kurkin/home/.hermes -> ~/kurkin/hermes`, а Claude хранит свои user-level файлы в `~/kurkin/home/.claude`.
`ourosss-bootstrap-python` создаёт или переиспользует conda env `ourosss-py312`, ставит туда pinned `uv==0.11.4` и делает `uv sync --locked`.

Если на хосте нет `systemd --user`, используй:
```bash
~/kurkin/bin/ourosss-run start
~/kurkin/bin/ourosss-run status
~/kurkin/bin/ourosss-run logs
~/kurkin/bin/ourosss-run stop
```

### Проверить что попадёт в следующий sync
```bash
# На ноуте
hermes skills snapshot export infra/hermes/skills-snapshot.yaml
cp ~/.hermes/memories/USER.md infra/hermes/memories/USER.md
git diff infra/
```

### Добавить новый секрет
```bash
# 1. Положи в ~/.hermes/.env или ourosss/.env на ноуте
# 2. Прогони sync-push один раз
SERVER_HOST=kurkin-vllm bash infra/local/sync-push.sh
# 3. На сервере перезапусти бот чтобы подхватил новый EnvironmentFile
ssh kurkin-vllm 'systemctl --user restart ourosss'
```

## Claude skills

- Source of truth: `~/.claude/skills/` на ноуте, в репо только зеркало `infra/claude/skills/`.
- Восстановить на новом ноуте: `bash infra/local/restore-claude-skills.sh` (или `--force`, чтобы перезаписать).
- Добавить новый скилл: создать в `~/.claude/skills/` → следующий `sync-push` сам подхватит.
- Инвентарь: `cat infra/claude/skills/README.md`.
- Важно: это **не** project-scoped Claude skills, а чисто бэкап/инвентаризация.

## Troubleshooting

| Симптом | Где смотреть | Что чинить |
|---|---|---|
| Бот не стартует | `journalctl --user -u ourosss -n 100` | секреты в `~/kurkin/secrets/.env`? `uv run ourosss` руками работает? |
| Sync timer молчит | `systemctl --user list-timers`, `journalctl --user -u ourosss-sync` | таймер `enabled`? `loginctl enable-linger` сделан? |
| Git pull падает | `tail ~/kurkin/logs/sync.log` | dirty tree на сервере? скрипт сделает hard reset на следующем тике |
| Hermes на сервере не видит память | `ls -la ~/.hermes/memories/USER.md` | симлинк битый? перезапусти `bootstrap-server.sh` |
| Launchd на ноуте не пушит | `tail ~/Library/Logs/ourosss-sync.log`, `launchctl list \| grep ourosss` | плист загружен? права на скрипт `chmod +x`? |
| Rsync не доходит | `ssh kurkin-vllm 'echo ok'` | SSH alias настроен? `~/.ssh/config` имеет `Host kurkin-vllm`? |

## Не лезь сюда руками

- `~/kurkin/hermes/state.db*` — рантайм SQLite, не синкается, machine-local
- `~/kurkin/hermes/sessions/` — история чатов, machine-local
- `~/kurkin/hermes/cache/`, `audio_cache/`, `image_cache/` — кэши, мусор
- `infra/hermes/memories/USER.md` **на сервере** — это симлинк в репо, edit ломает следующий git pull. Редактируй только на ноуте.
