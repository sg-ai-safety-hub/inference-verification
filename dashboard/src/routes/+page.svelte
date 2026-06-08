<script lang="ts">
	import Chat from './Chat.svelte';
	import HostCluster from './HostCluster.svelte';
	import RecomputationCluster from './RecomputationCluster.svelte';
</script>

<div class="flex flex-wrap  items-center justify-center gap-5 bg-muted p-4">
	<Chat />
	<HostCluster />
	<RecomputationCluster />
</div>
