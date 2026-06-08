<script lang="ts">
	import { HOST_CLUSTER_URL } from '$app/env/public';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { api } from '$lib/utils';
	import { io, type Socket } from 'socket.io-client';
	import { onDestroy, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	type State = {
		status: 'Ready' | 'Running' | 'Done';
		is_training: boolean;
		request: string | null;
		response: string | null;
	};

	let connected = $state(false);
	let clusterState: State = $state({
		status: 'Ready',
		is_training: false,
		request: null,
		response: null
	});

	let socket: Socket;

	onMount(() => {
		socket = io(HOST_CLUSTER_URL);
		socket.on('connect', () => (connected = true));
		socket.on('disconnect', () => (connected = false));
		socket.on('state', (data: State) => (clusterState = data));
	});

	onDestroy(() => socket?.disconnect());

	async function setTraining(isTraining: boolean) {
		try {
			await api.post(`${HOST_CLUSTER_URL}/set-training`, { json: isTraining });
		} catch (e) {
			toast.error('Error: Could not reach the server.');
			console.error(e);
		}
	}
</script>

<Card class="flex max-w-full  h-96 w-2xl flex-col gap-0">
	<CardHeader class="pb-3">
		<CardTitle class="text-base font-semibold tracking-tight">Host Cluster</CardTitle>
	</CardHeader>
	<CardContent class="flex min-h-0 flex-1 flex-row gap-3 p-3 pt-0">
		<!-- Status panel -->
		<div
			class="flex flex-1 flex-col gap-3 overflow-y-auto rounded-md border border-border text-sm bg-zinc-100 p-3 font-mono"
		>
			<!-- Connection / status -->
			<div class="flex items-center gap-2">
				<span class="size-2 shrink-0 rounded-full {connected ? 'bg-green-500' : 'bg-zinc-600'}"
				></span>
				<span class="">{connected ? clusterState.status : 'Disconnected'}</span>
			</div>

			<!-- Mode -->
			<div class="flex items-center gap-2">
				<span >Mode:</span>
				<span class="font-bold {clusterState.is_training ? 'text-red-500' : 'text-green-600'}">
					{clusterState.is_training ? 'Training' : 'Inference'}
				</span>
			</div>

			<!-- Received request -->
			<div class="flex flex-col gap-1">
				<span>Received Request:</span>
				{#if clusterState.request}
					<span class="wrap-break-word text-blue-600">{clusterState.request}</span>
				{:else}
					<span class="text-zinc-600">—</span>
				{/if}
			</div>

			<!-- Received response -->
			<div class="flex flex-col gap-1">
				<span >Sending response:</span>
				{#if clusterState.response}
					<span class="wrap-break-word text-blue-600">{clusterState.response}</span>
				{:else}
					<span class="text-zinc-600">—</span>
				{/if}
			</div>
		</div>

		<!-- Controls -->
		<div class="flex flex-col gap-2">
			<button
				class="rounded-md px-4 py-2 text-sm font-medium text-white transition-colors {!clusterState.is_training
					? 'bg-green-600 ring-2 ring-green-300'
					: 'bg-green-600/40 hover:bg-green-500'}"
				onclick={() => setTraining(false)}
			>
				Run Inference
			</button>
			<button
				class="rounded-md px-4 py-2 text-sm font-medium text-white transition-colors {clusterState.is_training
					? 'bg-red-600 ring-2 ring-red-300'
					: 'bg-red-600/40 hover:bg-red-500'}"
				onclick={() => setTraining(true)}
			>
				Run Training
			</button>
		</div>
	</CardContent>
</Card>
