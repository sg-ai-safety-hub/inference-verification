cp .env.example .env
cp components/gateway/.env.example components/gateway/.env
cp components/main_cluster/.env.example components/main_cluster/.env
cp components/recomputation_cluster/.env.example components/recomputation_cluster/.env
pnpm add -g concurrently