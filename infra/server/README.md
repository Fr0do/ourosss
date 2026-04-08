# Server Deployment (kurkin-*)

Prereqs on server:
- git, ssh access to `git@github.com:Fr0do/ourosss`
- Hermes CLI: `curl -fsSL https://hermes.sh | bash`
- uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- (optional) gh auth login

One-time setup:
```bash
ssh kurkin-vllm
mkdir -p ~/kurkin && cd ~/kurkin
git clone git@github.com:Fr0do/ourosss.git
bash ourosss/infra/server/bootstrap-server.sh
```

Push secrets from laptop (or wait for launchd):
```bash
SERVER_HOST=kurkin-vllm bash infra/local/sync-push.sh
```

Enable launchd on macOS laptop:
```bash
cp infra/local/com.ourosss.hermes-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ourosss.hermes-sync.plist
```

Verify:
- `systemctl --user status ourosss`
- `journalctl --user -u ourosss -f`
- `systemctl --user list-timers | grep ourosss`

Troubleshooting:
- Linger: `sudo loginctl enable-linger $USER`
- Secrets missing: ensure `~/kurkin/secrets/{.env,auth.json,hermes.env}` are rsynced
- Hermes auth: run `hermes login` if imports fail
- Network ports: check other Telegram bot instances

Data flow (pull = server timer, push = laptop launchd):
```
[macOS ~/ourosss repo] --git push--> [GitHub] --git pull--> [server ~/kurkin/ourosss]
        |                                         |
        +--rsync secrets--> [server ~/kurkin/secrets]      
        |                                         |
        +--launchd 30m--> sync-push.sh            +--systemd 15m--> sync-pull.sh
```
