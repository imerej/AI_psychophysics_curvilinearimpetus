#!/bin/bash
# Run stages in order:  bash run_stages.sh "vjepa_g:1 ltx13b:4 vlm:1.5 cosmos2b:3"   (stage:max_hours)
# A stage already marked DONE is skipped; a stage that hits its time limit is stopped and the next one starts
# (its finished clips are kept and it resumes if run again). Progress: runs/<stage>/progress.log, status.txt.
# Each stage's results are zipped BEFORE its "end" line is written, so the watcher never asks for a zip that
# is missing or half-written.
cd "$(dirname "$0")"
export HF_HOME=/workspace/hf HF_HUB_ENABLE_HF_TRANSFER=1 JOB_DIR=$(pwd) PYTHONUNBUFFERED=1
for spec in $1; do
  st=${spec%%:*}; hrs=${spec##*:}
  [ -f runs/$st/DONE ] && { echo "$(date +%T) $st already done" >> status.txt; continue; }
  py=${PY_GEN:-/workspace/venv-gen/bin/python}; [ "$st" = "vlm" ] && py=${PY_VLM:-/workspace/venv-vlm/bin/python}
  echo "$(date +%T) $st start (limit ${hrs} h)" >> status.txt
  timeout --signal=INT --kill-after=60 $(python3 -c "print(int(float('$hrs')*3600))") $py stage_$st.py ${STAGE_ARGS} >> runs_$st.log 2>&1
  rc=$?
  mkdir -p runs/$st
  (cd runs && python3 -m zipfile -c ../results_$st.zip.part $st) && mv results_$st.zip.part results_$st.zip
  echo "$(date +%T) $st end, exit $rc$([ $rc = 124 ] && echo ' (time limit)')" >> status.txt
done
echo "$(date +%T) ALL FINISHED" >> status.txt
