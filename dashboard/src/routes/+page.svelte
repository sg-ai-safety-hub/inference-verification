<script lang="ts">
	import Chat from './Chat.svelte';
	import MainCluster from './MainCluster.svelte';
	import RecomputationCluster from './RecomputationCluster.svelte';
</script>

<div class="flex flex-wrap min-h-screen items-start content-center justify-center gap-5 bg-muted p-4">
	<Chat />
	<MainCluster />
	<RecomputationCluster />
</div>
