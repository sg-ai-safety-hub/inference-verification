<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Textarea } from '$lib/components/ui/textarea';
	import { SendHorizontal } from '@lucide/svelte';
	import ky from 'ky';
	import { toast } from 'svelte-sonner';
	import { fade, fly } from 'svelte/transition';

	type Message = { role: 'user' | 'assistant'; content: string };

	let messages: Message[] = $state([{ role: 'assistant', content: 'Hello! How can I help you?' }]);
	let input = $state('');
	let loading = $state(false);

	async function send() {
		const text = input.trim();
		if (!text || loading) return;

		messages.push({ role: 'user', content: text });
		input = '';
		loading = true;

		try {
			const data = await ky
				.post('http://localhost:8000/request', { json: { messages } })
				.json<{ response_text: string }>();
			messages.push({ role: 'assistant', content: data.response_text });
		} catch (e) {
			messages.pop();
			input = text;
			toast.error('Error: Could not reach the server.');
			console.error(e);
		} finally {
			loading = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			send();
		}
	}

	let messagesEl: HTMLDivElement;
	$effect(() => {
		if (messagesEl && messages.length >= 0)
			messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
	});
</script>

<div class="flex h-screen items-center justify-center bg-muted p-4">
	<Card class="flex w-full max-w-2xl flex-col gap-0" style="height: min(720px, 90vh)">
		<CardHeader class="shrink-0 pb-4">
			<CardTitle class="text-base font-semibold tracking-tight">Chat</CardTitle>
		</CardHeader>
		<CardContent class="flex min-h-0 flex-1 flex-col overflow-hidden p-0">
			<div
				bind:this={messagesEl}
				class="flex flex-1 scrollbar-none flex-col gap-3 overflow-y-auto border-t border-border/40 px-4 py-4"
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
							class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed {msg.role ===
							'user'
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
						<div class="flex items-center gap-1 rounded-2xl bg-muted px-4 py-3">
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
					class="size-8 shrink-0 rounded-lg transition-all duration-150 hover:scale-105 active:scale-95 disabled:scale-100 opacity-80"
					variant="ghost"
					size="icon"
					disabled={loading || !input.trim()}
				>
					<SendHorizontal class="size-4" fill="var(--primary-light)" color="var(--primary-light)" />
				</Button>
			</div>
		</CardFooter>
	</Card>
</div>
