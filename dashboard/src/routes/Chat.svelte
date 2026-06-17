<script lang="ts">
	import {
		env 
	} from '$env/dynamic/public';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardAction,
		CardContent,
		CardFooter,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Textarea } from '$lib/components/ui/textarea';
	import { api, cn, isInvalidApiKeyError } from '$lib/utils';
	import RotateCcw from '@lucide/svelte/icons/rotate-ccw';
	import SendHorizontal from '@lucide/svelte/icons/send-horizontal';
	import { HTTPError } from 'ky';
	import { toast } from 'svelte-sonner';
	import { fade, fly } from 'svelte/transition';

	type Message = { role: 'user' | 'assistant'; content: string };

	let { class: className }: { class?: string } = $props();

	let messages: Message[] = $state([{ role: 'assistant', content: 'Hello! How can I help you?' }]);
	let input = $state('');
	let loading = $state(false);
	let recomputationError = $state(false);

	async function send() {
		const text = input.trim();
		if (!text || loading) return;
		// Remove previous user message if any (this is result of a previous error)
		if (messages.at(-1)?.role == 'user') {
			messages.pop();
		}
		messages.push({ role: 'user', content: text });
		input = '';
		recomputationError = false;
		loading = true;
		try {
			// Reset cluster state to ready before submitting
			await Promise.all([
				api.post(`${env.HOST_CLUSTER_URL}/clear`),
				api.post(`${env.RECOMPUTATION_CLUSTER_URL}/clear`)
			]);
			const data = await api
				.post(`${env.HOST_GATEWAY_URL}/request`, { json: { messages }, timeout: false })
				.json<{ responseText: string }>();
			messages.push({ role: 'assistant', content: data.responseText });
		} catch (e) {
			input = text;
			// Handle recomputation error
			if (e instanceof HTTPError && e.response.status === 400) {
				if (e.data.detail === 'Recomputation failed') {
					recomputationError = true;
					return;
				}
			}
			messages.pop();
			if (isInvalidApiKeyError(e)) {
				toast.error('Authentication failed - API key must be set for write access.');
			} else {
				toast.error('Error: Could not reach the server.');
				console.error(e);
			}
		} finally {
			loading = false;
		}
	}

	async function reset() {
		if (loading) return;
		messages.splice(1); // Retain only the initial message
		input = '';
		recomputationError = false;
		try {
			await Promise.all([
				api.post(`${env.HOST_CLUSTER_URL}/clear`),
				api.post(`${env.RECOMPUTATION_CLUSTER_URL}/clear`)
			]);
		} catch (e) {
			if (isInvalidApiKeyError(e)) return;
			toast.error('Error: Could not clear cluster states');
			console.error(e);
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			send();
		}
	}

	// Scroll when new messages are added
	let messagesEl: HTMLDivElement;
	$effect(() => {
		if (messagesEl && messages.length > 0) {
			messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
		}
	});
</script>

<Card class={cn('flex h-96 w-2xl max-w-full flex-col gap-0', className)}>
	<CardHeader class="pb-2">
		<CardTitle class="text-base font-semibold tracking-tight">Chat</CardTitle>
		<CardAction>
			<Button
				onclick={reset}
				class="size-7 rounded-lg text-muted-foreground/0 transition-colors duration-150 hover:text-muted-foreground disabled:opacity-100"
				variant="ghost"
				size="icon"
				disabled={loading}
				title="Reset conversation"
			>
				<RotateCcw class="size-3.5" />
			</Button>
		</CardAction>
	</CardHeader>
	<CardContent class="flex min-h-0 flex-1 flex-col overflow-hidden p-0">
		<div
			bind:this={messagesEl}
			class="flex flex-1 scrollbar-none flex-col gap-3 overflow-y-auto border-t border-border/40 px-4 py-3"
		>
			{#if messages.length === 0}
				<p class="m-auto text-sm text-muted-foreground" transition:fade={{ duration: 150 }}>
					Send a message to start the conversation.
				</p>
			{/if}
			{#each messages as msg, i (i)}
				<div
					class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}"
					in:fly={{ y: 8, duration: 220 }}
				>
					<div
						class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed {msg.role === 'user'
							? 'bg-primary-light text-primary-foreground'
							: 'bg-muted text-foreground'}"
					>
						{msg.content}
					</div>
				</div>
			{/each}
			{#if loading}
				<!-- Loading indicator -->
				<div class="flex justify-start" in:fade={{ duration: 120 }}>
					<div class="m-1.5 flex items-center gap-1 rounded-2xl bg-muted px-4 py-3">
						<span
							class="size-1.5 animate-bounce rounded-full bg-muted-foreground/60"
							style="animation-delay: 0ms"
						></span>
						<span
							class="size-1.5 animate-bounce rounded-full bg-muted-foreground/60"
							style="animation-delay: 150ms"
						></span>
						<span
							class="size-1.5 animate-bounce rounded-full bg-muted-foreground/60"
							style="animation-delay: 300ms"
						></span>
					</div>
				</div>
			{/if}
			{#if recomputationError}
				<div class="flex justify-start" in:fade={{ duration: 120 }}>
					<div
						class="max-w-[80%] rounded-2xl bg-destructive/10 px-4 py-2.5 text-sm leading-relaxed text-destructive"
					>
						Error: Recomputation failed
					</div>
				</div>
			{/if}
		</div>
	</CardContent>

	<CardFooter class="shrink-0 p-3">
		<div
			class="flex w-full items-end gap-2 rounded-xl border border-border bg-background px-3 py-2 transition-all duration-200 focus-within:border-ring/40 focus-within:ring-2 focus-within:ring-ring/20"
		>
			<Textarea
				bind:value={input}
				onkeydown={handleKeydown}
				placeholder="Type a message…"
				class="min-h-0 flex-1 resize-none border-0 bg-transparent p-0 leading-9 shadow-none focus-visible:ring-0"
			/>
			<Button
				type="submit"
				onclick={send}
				class="size-8 shrink-0 rounded-lg opacity-80 transition-all duration-150 hover:scale-105 active:scale-95 disabled:scale-100"
				variant="ghost"
				size="icon"
				disabled={loading || !input.trim()}
			>
				<SendHorizontal class="size-4" fill="var(--primary-light)" color="var(--primary-light)" />
			</Button>
		</div>
	</CardFooter>
</Card>
