#!/bin/bash
# Backstop on the pod, in case the local watcher (orchestrate.py watch) dies: terminates this pod, so all billing
# stops, when the run's money cap is reached (bash selfdestruct.sh SECONDS_LEFT) or 90 min after the stages end
# (time for the watcher to download the last results). Runpod gives every pod runpodctl and a key for itself.
cd "$(dirname "$0")"
deadline=$(( $(date +%s) + $1 )); fin=""
while true; do
  now=$(date +%s)
  if [ "$now" -ge "$deadline" ]; then why="money cap reached"; break; fi
  if grep -qE "ALL FINISHED|SETUP FAILED" status.txt 2>/dev/null; then
    [ -z "$fin" ] && fin=$now
    [ $((now - fin)) -ge 5400 ] && { why="stages ended 90 min ago"; break; }
  fi
  sleep 60
done
echo "$(date +%T) SELF-TERMINATE: $why" >> status.txt
runpodctl remove pod "$RUNPOD_POD_ID" >> selfdestruct.log 2>&1 || \
  curl -s https://api.runpod.io/graphql -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
       -d "{\"query\": \"mutation { podTerminate(input: {podId: \\\"$RUNPOD_POD_ID\\\"}) }\"}" >> selfdestruct.log 2>&1
