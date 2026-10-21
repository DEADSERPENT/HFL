#!/usr/bin/env bash
# run_detached.sh — run the pipeline so it survives VS Code, SSH and terminal death.
#
#   ./run_detached.sh start --dataset vitaldb [any run_pipeline.py flag ...]
#   ./run_detached.sh status
#   ./run_detached.sh tail
#   ./run_detached.sh stop
#
# Why: run_pipeline.py is already resumable, but a run started in VS Code's
# integrated terminal dies with the editor. setsid detaches it from the
# controlling terminal and the process group, so nothing the GUI does can
# reach it. Nothing here is hardcoded: paths resolve from this script's
# location and every flag is passed straight through to run_pipeline.py.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$SIM_DIR")"
VENV="$ROOT_DIR/hfl_env/bin/activate"
PIPELINE="${HFL_PIPELINE:-$SCRIPT_DIR/run_pipeline.py}"   # overridable for testing

RUN_DIR="$SIM_DIR/results/pipeline/_detached"
PIDFILE="$RUN_DIR/run.pid"
CURRENT="$RUN_DIR/current.log"
mkdir -p "$RUN_DIR"

alive() { [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

cmd="${1:-}"; [[ $# -gt 0 ]] && shift || true

case "$cmd" in
  start)
    if alive; then
      echo "Already running (PID $(cat "$PIDFILE")). Use 'status', 'tail' or 'stop'." >&2
      exit 1
    fi
    [[ $# -gt 0 ]] || { echo "usage: $0 start --dataset <name> [flags...]" >&2; exit 2; }
    [[ -f "$VENV" ]]     || { echo "venv not found: $VENV" >&2; exit 3; }
    [[ -f "$PIPELINE" ]] || { echo "pipeline not found: $PIPELINE" >&2; exit 3; }

    LOG="$RUN_DIR/run_$(date +%Y%m%d_%H%M%S).log"
    ln -sfn "$LOG" "$CURRENT"
    rm -f "$PIDFILE"

    # %q-quote the pass-through flags so args containing spaces survive.
    ARGS=$(printf '%q ' "$@")

    # setsid: new session, no controlling terminal -> immune to the editor dying.
    # setsid forks, so $! here is the short-lived wrapper, NOT the run. The
    # child publishes its own $$ instead; exec keeps that pid as python's.
    setsid nohup bash -c "
      echo \$\$ > '$PIDFILE'
      source '$VENV'
      cd '$SIM_DIR'
      echo \"[detached] started \$(date -Is)\"
      echo \"[detached] argv: run_pipeline.py $ARGS\"
      echo \"[detached] host: \$(hostname)  pid: \$\$\"
      echo '---'
      exec python -u '$PIPELINE' $ARGS
    " >"$LOG" 2>&1 < /dev/null &

    for _ in $(seq 1 60); do [[ -s "$PIDFILE" ]] && break; sleep 0.1; done
    [[ -s "$PIDFILE" ]] || { echo "failed to start; see $LOG" >&2; tail -n 20 "$LOG" >&2; exit 4; }
    echo "Started PID $(cat "$PIDFILE")"
    echo "Log: $LOG"
    echo "Follow with: $0 tail"
    ;;

  status)
    if alive; then
      pid=$(cat "$PIDFILE")
      echo "RUNNING  pid=$pid  elapsed=$(ps -o etime= -p "$pid" | tr -d ' ')"
      echo "log: $(readlink -f "$CURRENT" 2>/dev/null || echo none)"
      echo "--- last 15 lines ---"
      tail -n 15 "$CURRENT" 2>/dev/null || true
    else
      echo "NOT RUNNING"
      if [[ -e "$CURRENT" ]]; then
        echo "last log: $(readlink -f "$CURRENT")"
        echo "--- tail ---"
        tail -n 15 "$CURRENT"
      fi
    fi
    ;;

  tail)  tail -f "$CURRENT" ;;

  stop)
    if alive; then
      pid=$(cat "$PIDFILE")
      # negative PID: kill the whole process group, including child python stages
      kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid"
      echo "Sent SIGTERM to process group $pid. Re-run 'start' later to resume (finished stages are skipped)."
    else
      echo "Nothing running."
    fi
    ;;

  *)
    sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 2 ;;
esac
