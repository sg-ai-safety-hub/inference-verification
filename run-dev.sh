concurrently --kill-others --names "dashboard,host_gateway,network_tap,host_cluster,recomputation_cluster" \
"pnpm -C dashboard dev" \
"uv run fastapi dev components/host_gateway/main.py --port 8010" \
"uv run fastapi dev components/network_tap/main.py --port 8020" \
"uv run fastapi dev components/host_cluster/main.py --port 8030" \
"uv run fastapi dev components/recomputation_cluster/main.py --port 8040"
