<script lang="ts">
	let { onSelect }: { onSelect: (prompt: string) => void } = $props();

	const prompts = [
		{
			icon: '\u{1F305}',
			text: 'Generate a sunset over mountains with vibrant colors'
		},
		{
			icon: '\u{1F3A8}',
			text: 'Create a watercolor painting of a cat reading a book'
		},
		{
			icon: '\u{2615}',
			text: 'Design a minimalist logo for a coffee shop'
		},
		{
			icon: '\u{1F303}',
			text: 'Draw a futuristic cityscape at night'
		}
	];
</script>

<div class="example-prompts">
	<p class="prompt-heading">Try an example</p>
	<div class="prompt-grid">
		{#each prompts as prompt}
			<button class="prompt-card" onclick={() => onSelect(prompt.text)}>
				<span class="prompt-icon">{prompt.icon}</span>
				<span class="prompt-text">{prompt.text}</span>
			</button>
		{/each}
	</div>
</div>

<style>
	.example-prompts {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 32px 16px;
	}

	.prompt-heading {
		color: #888;
		font-size: 14px;
		margin-bottom: 16px;
	}

	.prompt-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 12px;
		max-width: 600px;
		width: 100%;
	}

	@media (max-width: 500px) {
		.prompt-grid {
			grid-template-columns: 1fr;
		}
	}

	.prompt-card {
		display: flex;
		align-items: flex-start;
		gap: 8px;
		padding: 12px;
		border-radius: 12px;
		border: 1px solid #333;
		background-color: #16213e;
		color: #eee;
		cursor: pointer;
		text-align: left;
		font-size: 13px;
		line-height: 1.4;
		transition: background-color 0.15s ease;
	}

	.prompt-card:hover {
		background-color: #0f3460;
	}

	.prompt-icon {
		font-size: 18px;
		flex-shrink: 0;
	}

	.prompt-text {
		flex: 1;
	}
</style>
