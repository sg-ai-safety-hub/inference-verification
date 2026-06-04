# Inference Verification

![architecture](docs/architecture.svg)

## Getting started

### Install:

Install pnpm + uv

```bash
pnpm add -g concurrently
docker pull vllm/vllm-openai-cpu:v0.22.0-x86_64
docker create \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -v ~/.cache/vllm:/root/.cache/vllm \
    -e KMP_TOPOLOGY_METHOD=flat \
    -e HF_TOKEN=$HF_TOKEN \
    -p 8080:8000 \
    --name vllm \
    vllm/vllm-openai-cpu:v0.22.0-x86_64 \
    google/gemma-3-270m-it \
    --gpu-memory-utilization 0.3 \
    --max-model-len 1000
```

<details> <summary>Notes</summary>

- Set HF_Token for faster download
- `KMP_TOPOLOGY_METHOD=flat` avoids `Assertion failure at kmp_affinity.cpp` errors when run in sandboxes

</details>

### Run:

```bash
docker start -i vllm
uv run fastapi dev main.py
pnpm -C dashboard dev
```
