<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { Toaster } from '$lib/components/ui/sonner';
	import './layout.css';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Verification Demo</title>
</svelte:head>
{@render children()}
<Toaster richColors />
