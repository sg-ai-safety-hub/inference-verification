<script lang="ts">
	import Chat from './Chat.svelte';
	import HostCluster from './HostCluster.svelte';
	import RecomputationCluster from './RecomputationCluster.svelte';
</script>

<div class="flex-col flex gap-5 items-center justify-center bg-muted p-4">
	<Chat />
	<HostCluster />
	<RecomputationCluster />
</div>
