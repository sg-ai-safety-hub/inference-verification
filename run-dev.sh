concurrently --kill-others --names "dashboard,gateway,network_logger,main_cluster,recomputation_cluster" \
"pnpm -C dashboard dev" \
"uv run fastapi dev components/gateway/main.py --port 8010" \
"uv run fastapi dev components/network_logger/main.py --port 8020" \
"uv run fastapi dev components/main_cluster/main.py --port 8030" \
"uv run fastapi dev components/recomputation_cluster/main.py --port 8040"
