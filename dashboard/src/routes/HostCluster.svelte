<script lang="ts">
	import { HOST_CLUSTER_URL } from '$app/env/public';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { api } from '$lib/utils';
	import { toast } from 'svelte-sonner';

	type LogEntry = { time: string; level: 'INFO' | 'WARN' | 'ERROR'; message: string };

	let logs: LogEntry[] = $state([]);

	let logsEl: HTMLDivElement;

	async function setTraining(isTraining: boolean) {
		try {
			await api.post(`${HOST_CLUSTER_URL}/set-training`, { json: isTraining });
			const now = new Date().toTimeString().slice(0, 8);
			logs = [
				...logs,
				{
					time: now,
					level: 'INFO',
					message: isTraining ? 'Training started by user' : 'Training stopped by user'
				}
			];
			setTimeout(() => logsEl?.scrollTo({ top: logsEl.scrollHeight, behavior: 'smooth' }), 0);
		} catch (e) {
			toast.error('Error: Could not reach the server.');
			console.error(e);
		}
	}

	const levelClass: Record<LogEntry['level'], string> = {
		INFO: 'text-blue-400',
		WARN: 'text-yellow-400',
		ERROR: 'text-red-400'
	};
</script>

<Card class="flex flex-col gap-0 h-96 w-2xl">
	<CardHeader class="pb-3">
		<CardTitle class="text-base font-semibold tracking-tight">Host Cluster</CardTitle>
	</CardHeader>
	<CardContent class="flex min-h-0 flex-1 flex-row gap-3 p-3 pt-0">
		<!-- Log panel -->
		<div
			bind:this={logsEl}
			class="flex-1 overflow-y-auto rounded-md border border-border bg-zinc-950 p-3 font-mono text-xs"
		>
			<div class="mb-1 text-zinc-500">Logs:</div>
			{#each logs as entry, i (i)}
				<div class="flex gap-2 leading-5">
					<span class="shrink-0 text-zinc-500">{entry.time}</span>
					<span class="w-10 shrink-0 {levelClass[entry.level]}">{entry.level}</span>
					<span class="text-zinc-200">{entry.message}</span>
				</div>
			{/each}
		</div>

		<!-- Controls -->
		<div class="flex flex-col gap-2">
			<button
				class="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-500 active:bg-green-700"
				onclick={() => setTraining(true)}
			>
				Start Training
			</button>
			<button
				class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 active:bg-red-700"
				onclick={() => setTraining(false)}
			>
				Stop Training
			</button>
		</div>
	</CardContent>
</Card>
