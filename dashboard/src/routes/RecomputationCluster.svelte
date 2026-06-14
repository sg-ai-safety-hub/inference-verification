<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { cn } from '$lib/utils';
	import { io, type Socket } from 'socket.io-client';
	import { onDestroy, onMount } from 'svelte';

	type State = {
		status: 'Ready' | 'Running' | 'Done';
		request: string | null;
		received_response: string | null;
		recomputed_response: string | null;
		verified: boolean | null;
	};

	let { class: className }: { class?: string } = $props();

	let connected = $state(false);
	let clusterState: State = $state({
		status: 'Ready',
		request: null,
		received_response: null,
		recomputed_response: null,
		verified: null
	});

	let socket: Socket;

	onMount(() => {
		socket = io(env.RECOMPUTATION_CLUSTER_URL);
		socket.on('connect', () => (connected = true));
		socket.on('disconnect', () => (connected = false));
		socket.on('state', (data: State) => (clusterState = data));
	});

	onDestroy(() => socket?.disconnect());
</script>

<Card class={cn('flex h-96 w-2xl max-w-full flex-col gap-0', className)}>
	<CardHeader class="px-5 pb-3">
		<CardTitle class="text-base font-semibold tracking-tight">Recomputation Cluster</CardTitle>
	</CardHeader>
	<CardContent class="flex min-h-0 flex-1 flex-row gap-3 p-5 pt-0">
		<!-- Status panel -->
		<div
			class="flex flex-1 flex-col gap-3 overflow-y-auto rounded-md border border-border bg-zinc-100 p-3 font-mono text-base"
		>
			<!-- Connection / status -->
			<div class="flex items-center gap-2">
				<span class="size-2 shrink-0 rounded-full {connected ? 'bg-green-500' : 'bg-zinc-600'}"
				></span>
				<span class="">{connected ? clusterState.status : 'Disconnected'}</span>
			</div>

			<!-- Received request -->
			{#if clusterState.request}
				<div class="flex flex-col">
					<span>Received Request:</span>
					<span class="break-all text-blue-600">{clusterState.request}</span>
				</div>
			{/if}

			<!-- Received response -->
			{#if clusterState.received_response}
				<div class="flex flex-col">
					<span>Received Response:</span>
					<span class="break-all text-blue-600">{clusterState.received_response}</span>
				</div>
			{/if}

			<!-- Recomputed response -->
			{#if clusterState.recomputed_response}
				<div class="flex flex-col">
					<span>Recomputed Response:</span>
					<span class="break-all text-blue-600">{clusterState.recomputed_response}</span>
				</div>
			{/if}

			<!-- Verification result -->
			{#if clusterState.verified !== null}
				<div class="flex items-center gap-2">
					<span>Verification:</span>
					<span class="font-bold {clusterState.verified ? 'text-green-600' : 'text-red-500'}">
						{clusterState.verified ? 'Successful' : 'Failed'}
					</span>
				</div>
			{/if}
		</div>
	</CardContent>
</Card>
