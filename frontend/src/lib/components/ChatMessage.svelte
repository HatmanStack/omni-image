<script lang="ts">
	import type { ChatMessage } from '$lib/types';

	let { message }: { message: ChatMessage } = $props();
</script>

<article
	class="chat-message"
	class:user={message.role === 'user'}
	class:assistant={message.role === 'assistant'}
	aria-label="{message.role} message"
>
	<div class="bubble">
		{#if message.isLoading}
			<div class="loading" aria-label="Loading response">
				<span class="dot"></span>
				<span class="dot"></span>
				<span class="dot"></span>
			</div>
		{:else}
			{#if message.image}
				<figure class="message-image">
					<img
						src="data:image/{message.imageFormat ||
							'png'};base64,{message.image}"
						alt={message.role === 'user' ? 'Uploaded image' : 'Generated image'}
					/>
				</figure>
			{/if}
			{#if message.text}
				<p class="message-text">{message.text}</p>
			{/if}
		{/if}
	</div>
</article>

<style>
	.chat-message {
		display: flex;
		margin-bottom: 16px;
		padding: 0 16px;
	}

	.chat-message.user {
		justify-content: flex-end;
	}

	.chat-message.assistant {
		justify-content: flex-start;
	}

	.bubble {
		max-width: 75%;
		padding: 12px 16px;
		border-radius: 16px;
		word-wrap: break-word;
	}

	.user .bubble {
		background-color: #0f3460;
		color: #eee;
		border-bottom-right-radius: 4px;
	}

	.assistant .bubble {
		background-color: #16213e;
		color: #eee;
		border-bottom-left-radius: 4px;
	}

	.message-image {
		margin: 0 0 8px 0;
		padding: 0;
	}

	.message-image img {
		max-width: 100%;
		border-radius: 8px;
		display: block;
	}

	.user .message-image img {
		max-width: 200px;
	}

	.message-text {
		margin: 0;
		line-height: 1.5;
	}

	.loading {
		display: flex;
		gap: 4px;
		padding: 4px 0;
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background-color: #888;
		animation: bounce 1.4s infinite ease-in-out both;
	}

	.dot:nth-child(1) {
		animation-delay: -0.32s;
	}

	.dot:nth-child(2) {
		animation-delay: -0.16s;
	}

	@keyframes bounce {
		0%,
		80%,
		100% {
			transform: scale(0);
		}
		40% {
			transform: scale(1);
		}
	}
</style>
