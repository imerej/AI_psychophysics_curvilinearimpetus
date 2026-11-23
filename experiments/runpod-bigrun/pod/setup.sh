#!/bin/bash
# One-time setup on the pod (re-runnable): two Python environments on the pod's /workspace disk.
#   gen: diffusers + transformers (LTX, Wan, Cosmos, V-JEPA)     vlm: vLLM (Qwen / InternVL)
set -e
export UV_CACHE_DIR=/workspace/.uv-cache
pip install -q uv
if [ ! -f /workspace/venv-gen/.ok ]; then
  uv venv -q /workspace/venv-gen --python 3.11
  VIRTUAL_ENV=/workspace/venv-gen uv pip install -q torch torchvision "diffusers==0.43.0" "transformers>=5" accelerate \
      sentencepiece ftfy protobuf imageio imageio-ffmpeg scipy pillow hf_transfer cosmos_guardrail
  /workspace/venv-gen/bin/python -c "import torch, diffusers, transformers; print('gen ok', torch.__version__, diffusers.__version__, transformers.__version__, torch.cuda.is_available())"
  touch /workspace/venv-gen/.ok
fi
if [ "$NEED_VLM" = "1" ] && [ ! -f /workspace/venv-vlm/.ok ]; then
  uv venv -q /workspace/venv-vlm --python 3.11
  VIRTUAL_ENV=/workspace/venv-vlm uv pip install -q vllm imageio imageio-ffmpeg scipy pillow hf_transfer
  /workspace/venv-vlm/bin/python -c "import vllm; print('vlm ok', vllm.__version__)"
  touch /workspace/venv-vlm/.ok
fi
echo setup done
