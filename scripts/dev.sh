#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_ENV="$BACKEND_DIR/.env"
BACKEND_ENV_EXAMPLE="$BACKEND_DIR/.env.example"
BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"
API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:8000/api/v1}"

usage() {
  cat <<'USAGE'
Usage: ./scripts/dev.sh <command> [options]

Commands:
  init            Start MySQL, create backend/.env if missing, install dependencies, run migrations
  start           Start MySQL, run migrations, start backend and frontend in background
  stop            Stop backend and frontend
  stop --mysql    Stop backend, frontend, and the MySQL container
  restart         Stop backend/frontend, then start them again
  status          Show backend/frontend PID status and MySQL container status
  logs            Print log file paths and tail recent backend/frontend logs

Environment:
  VITE_API_BASE_URL  Frontend API base URL. Defaults to http://127.0.0.1:8000/api/v1
USAGE
}

ensure_run_dir() {
  mkdir -p "$RUN_DIR"
}

ensure_env() {
  if [[ ! -f "$BACKEND_ENV" ]]; then
    cp "$BACKEND_ENV_EXAMPLE" "$BACKEND_ENV"
  fi

  if grep -q '^BACKEND_CORS_ORIGINS=' "$BACKEND_ENV"; then
    if ! grep -q '^BACKEND_CORS_ORIGINS=.*127\.0\.0\.1:5173' "$BACKEND_ENV"; then
      sed -i.bak '/^BACKEND_CORS_ORIGINS=/ s/$/,http:\/\/127.0.0.1:5173/' "$BACKEND_ENV"
      rm -f "$BACKEND_ENV.bak"
    fi
  else
    printf '\nBACKEND_CORS_ORIGINS=http://127.0.0.1:5173\n' >> "$BACKEND_ENV"
  fi
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

is_pid_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file")"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

start_mysql() {
  require_command docker
  docker compose -f "$ROOT_DIR/docker-compose.yml" up -d mysql
}

install_backend() {
  require_command uv
  (cd "$BACKEND_DIR" && uv sync --extra dev)
}

install_frontend() {
  require_command npm
  (cd "$FRONTEND_DIR" && npm install)
}

migrate_database() {
  require_command uv
  (cd "$BACKEND_DIR" && uv run alembic upgrade head)
}

start_backend() {
  ensure_run_dir
  if is_pid_running "$BACKEND_PID"; then
    echo "Backend already running: PID $(cat "$BACKEND_PID")"
    return
  fi

  : > "$BACKEND_LOG"
  require_command setsid
  setsid bash -c 'cd "$1" && exec uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000' bash "$BACKEND_DIR" > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID"
  echo "Backend started: PID $(cat "$BACKEND_PID"), log $BACKEND_LOG"
}

start_frontend() {
  ensure_run_dir
  if is_pid_running "$FRONTEND_PID"; then
    echo "Frontend already running: PID $(cat "$FRONTEND_PID")"
    return
  fi

  : > "$FRONTEND_LOG"
  require_command setsid
  setsid bash -c 'cd "$1" && exec env VITE_API_BASE_URL="$2" npm run dev -- --host 127.0.0.1' bash "$FRONTEND_DIR" "$API_BASE_URL" > "$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID"
  echo "Frontend started: PID $(cat "$FRONTEND_PID"), log $FRONTEND_LOG"
}

stop_pid() {
  local name="$1"
  local pid_file="$2"

  if ! [[ -f "$pid_file" ]]; then
    echo "$name is not running"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    kill -- "-$pid" >/dev/null 2>&1 || kill "$pid" >/dev/null 2>&1 || true
    for _ in {1..20}; do
      if ! kill -0 "$pid" >/dev/null 2>&1; then
        break
      fi
      sleep 0.2
    done
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill -9 -- "-$pid" >/dev/null 2>&1 || kill -9 "$pid" >/dev/null 2>&1 || true
    fi
    echo "$name stopped"
  else
    echo "$name was not running"
  fi

  rm -f "$pid_file"
}

stop_mysql() {
  require_command docker
  docker compose -f "$ROOT_DIR/docker-compose.yml" stop mysql
}

cmd_init() {
  ensure_run_dir
  ensure_env
  start_mysql
  install_backend
  migrate_database
  install_frontend
  echo "Initialization complete"
}

cmd_start() {
  ensure_run_dir
  ensure_env
  start_mysql
  migrate_database
  start_backend
  start_frontend
  echo "Frontend: http://127.0.0.1:5173"
  echo "Backend API: http://127.0.0.1:8000/api/v1"
  echo "API docs: http://127.0.0.1:8000/docs"
}

cmd_stop() {
  stop_pid "Frontend" "$FRONTEND_PID"
  stop_pid "Backend" "$BACKEND_PID"
  if [[ "${1:-}" == "--mysql" ]]; then
    stop_mysql
  fi
}

cmd_status() {
  if is_pid_running "$BACKEND_PID"; then
    echo "Backend: running, PID $(cat "$BACKEND_PID")"
  else
    echo "Backend: stopped"
  fi

  if is_pid_running "$FRONTEND_PID"; then
    echo "Frontend: running, PID $(cat "$FRONTEND_PID")"
  else
    echo "Frontend: stopped"
  fi

  if command -v docker >/dev/null 2>&1; then
    docker compose -f "$ROOT_DIR/docker-compose.yml" ps mysql
  else
    echo "MySQL: docker command not found"
  fi
}

cmd_logs() {
  echo "Backend log: $BACKEND_LOG"
  echo "Frontend log: $FRONTEND_LOG"
  echo
  if [[ -f "$BACKEND_LOG" ]]; then
    echo "== Backend =="
    tail -n 40 "$BACKEND_LOG"
  fi
  if [[ -f "$FRONTEND_LOG" ]]; then
    echo "== Frontend =="
    tail -n 40 "$FRONTEND_LOG"
  fi
}

main() {
  local command="${1:-}"
  case "$command" in
    init)
      cmd_init
      ;;
    start)
      cmd_start
      ;;
    stop)
      shift
      cmd_stop "$@"
      ;;
    restart)
      cmd_stop
      cmd_start
      ;;
    status)
      cmd_status
      ;;
    logs)
      cmd_logs
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      echo "Unknown command: $command" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
