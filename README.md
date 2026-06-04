# Inference Verification
![architecture](docs/architecture.svg)

## Getting started
Suggested commands for local dev:

### Install:
Note: Set HF_Token for faster download
```bash
docker pull vllm/vllm-openai-cpu:v0.22.0-x86_64
docker run \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -v ~/.cache/vllm:/root/.cache/vllm \
    -e KMP_TOPOLOGY_METHOD=flat \
    -e HF_TOKEN=$HF_TOKEN \
    -p 8080:8000 \
    --name vllm \
    vllm/vllm-openai-cpu:v0.22.0-x86_64 \
    google/gemma-3-270m-it \
    --gpu-memory-utilization 0.4 \
    --max-model-len 1000
```
<details>
<summary>Notes</summary>
`KMP_TOPOLOGY_METHOD=flat` avoids `Assertion failure at kmp_affinity.cpp` errors when run in sandboxes
</details>

### Run:
```bash
docker start -i vllm
fastapi dev main.py
```

