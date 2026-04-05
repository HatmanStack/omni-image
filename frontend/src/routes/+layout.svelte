<script>
	let { children } = $props();
</script>

{@render children()}

<style>
	:global(*),
	:global(*::before),
	:global(*::after) {
		box-sizing: border-box;
	}

	:global(body),
	:global(html) {
		margin: 0;
		padding: 0;
		height: 100%;
	}

	:global(body) {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background-color: #1a1a2e;
		color: #eee;
	}
</style>
