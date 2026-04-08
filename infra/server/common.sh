#!/usr/bin/env bash

ourosss_real_home() {
  printf '%s\n' "${HOME}"
}

ourosss_base_dir() {
  local real_home
  real_home="$(ourosss_real_home)"
  printf '%s\n' "${OUROSSS_ROOT:-$real_home/kurkin}"
}

ourosss_profile_home() {
  local base
  base="$(ourosss_base_dir)"
  printf '%s\n' "${OUROSSS_PROFILE_HOME:-$base/home}"
}

ourosss_hermes_home() {
  local base
  base="$(ourosss_base_dir)"
  printf '%s\n' "$base/hermes"
}

ourosss_claude_settings() {
  local base
  base="$(ourosss_base_dir)"
  printf '%s\n' "$base/claude/settings.json"
}

ourosss_repo_dir() {
  local base
  base="$(ourosss_base_dir)"
  printf '%s\n' "$base/ourosss"
}

ourosss_secrets_dir() {
  local base
  base="$(ourosss_base_dir)"
  printf '%s\n' "$base/secrets"
}

ourosss_logs_dir() {
  local base
  base="$(ourosss_base_dir)"
  printf '%s\n' "$base/logs"
}

ourosss_server_script_dir() {
  local source_path link_dir
  source_path="${BASH_SOURCE[0]}"
  while [ -L "$source_path" ]; do
    link_dir="$(cd "$(dirname "$source_path")" && pwd)"
    source_path="$(readlink "$source_path")"
    [[ "$source_path" != /* ]] && source_path="$link_dir/$source_path"
  done
  cd "$(dirname "$source_path")" && pwd
}

ourosss_ensure_profile_layout() {
  local real_home base hermes_home profile_home
  real_home="$(ourosss_real_home)"
  base="$(ourosss_base_dir)"
  hermes_home="$(ourosss_hermes_home)"
  profile_home="$(ourosss_profile_home)"

  mkdir -p "$base" "$base/bin" "$base/claude" "$base/envs" "$hermes_home" "$profile_home/.claude"
  ln -snf "$hermes_home" "$profile_home/.hermes"

  if [ -d "$real_home/.ssh" ] && [ ! -e "$profile_home/.ssh" ]; then
    ln -snf "$real_home/.ssh" "$profile_home/.ssh"
  fi
}

ourosss_ensure_claude_settings() {
  local settings_path
  settings_path="$(ourosss_claude_settings)"
  mkdir -p "$(dirname "$settings_path")"
  if [ ! -f "$settings_path" ]; then
    printf '{\n  "mcpServers": {}\n}\n' > "$settings_path"
  fi
}
