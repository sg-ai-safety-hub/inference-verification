concurrently --kill-others --names "dashboard,host_gateway,host_cluster" \
"pnpm -C dashboard dev" \
"uv run fastapi dev components/host_gateway/main.py --port 8010" \
"uv run fastapi dev components/host_cluster/main.py --port 8030" 
