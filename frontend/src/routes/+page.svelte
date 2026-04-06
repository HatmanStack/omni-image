<script lang="ts">
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import ChatInput from '$lib/components/ChatInput.svelte';
	import ExamplePrompts from '$lib/components/ExamplePrompts.svelte';
	import SettingsPanel from '$lib/components/SettingsPanel.svelte';
	import { createChatStore } from '$lib/stores/chat.svelte';

	const store = createChatStore();

	let messageContainer: HTMLElement | undefined = $state();

	$effect(() => {
		// Auto-scroll when messages change, but only if user is near the bottom
		if (store.messages.length && messageContainer) {
			const { scrollTop, scrollHeight, clientHeight } = messageContainer;
			const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
			if (isNearBottom) {
				messageContainer.scrollTop = messageContainer.scrollHeight;
			}
		}
	});

	function handleSend(text: string, imageFile?: File) {
		store.sendMessage(text, imageFile);
	}

	function handleExampleSelect(prompt: string) {
		store.sendMessage(prompt);
	}
</script>

<div class="app-container">
	<header class="app-header">
		<h1 class="app-title">Omni Image</h1>
		<SettingsPanel settings={store.settings} onChange={store.updateSettings} />
	</header>

	<main class="message-area" bind:this={messageContainer}>
		{#if !store.hasMessages}
			<ExamplePrompts onSelect={handleExampleSelect} />
		{:else}
			<div class="message-list">
				{#each store.messages as message (message.id)}
					<ChatMessage {message} />
				{/each}
			</div>
		{/if}
	</main>

	{#if store.error}
		<div class="error-banner" role="alert">
			<span>{store.error}</span>
			<button onclick={() => store.clearError()} aria-label="Dismiss error"
				>&times;</button
			>
		</div>
	{/if}

	<footer class="input-area">
		<ChatInput onSend={handleSend} isLoading={store.isLoading} />
	</footer>
</div>

<style>
	.app-container {
		display: flex;
		flex-direction: column;
		height: 100vh;
		max-width: 900px;
		margin: 0 auto;
	}

	.app-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 12px 16px;
		border-bottom: 1px solid #333;
		flex-shrink: 0;
	}

	.app-title {
		font-size: 18px;
		font-weight: 600;
		margin: 0;
	}

	.message-area {
		flex: 1;
		overflow-y: auto;
		padding: 16px 0;
	}

	.message-list {
		display: flex;
		flex-direction: column;
	}

	.error-banner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 10px 16px;
		background-color: #e94560;
		color: white;
		font-size: 14px;
		flex-shrink: 0;
	}

	.error-banner button {
		background: none;
		border: none;
		color: white;
		font-size: 18px;
		cursor: pointer;
		padding: 0 4px;
	}

	.input-area {
		flex-shrink: 0;
	}
</style>
