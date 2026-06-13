<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { API_KEY_STORAGE } from '$lib/utils';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	onMount(() => {
		const key = page.url.searchParams.get('key');
		if (key) {
			globalThis.localStorage?.setItem(API_KEY_STORAGE, key);
			setTimeout(() => {
				toast.success('API key saved');
			});
		} else {
			setTimeout(() => {
				toast.error('No API key provided');
			});
		}
		goto(resolve('/'), { replaceState: true });
	});
</script>
