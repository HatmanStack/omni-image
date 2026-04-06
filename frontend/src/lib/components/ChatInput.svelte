<script lang="ts">
	let {
		onSend,
		isLoading
	}: {
		onSend: (text: string, imageFile?: File) => void;
		isLoading: boolean;
	} = $props();

	let text = $state('');
	let imageFile = $state<File | null>(null);
	let imagePreview = $state<string | null>(null);
	let fileInputEl: HTMLInputElement | undefined = $state();
	let textareaEl: HTMLTextAreaElement | undefined = $state();

	const canSend = $derived(
		!isLoading && (text.trim().length > 0 || imageFile !== null)
	);

	function handleSend() {
		if (!canSend) return;
		onSend(text.trim(), imageFile || undefined);
		text = '';
		imageFile = null;
		imagePreview = null;
		if (textareaEl) {
			textareaEl.style.height = 'auto';
		}
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	const MAX_FILE_SIZE_MB = 5;
	const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
	let fileError = $state<string | null>(null);

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) {
			fileError = null;
			if (file.size > MAX_FILE_SIZE_BYTES) {
				fileError = `File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Maximum is ${MAX_FILE_SIZE_MB}MB.`;
				if (fileInputEl) fileInputEl.value = '';
				return;
			}
			imageFile = file;
			const reader = new FileReader();
			reader.onload = () => {
				imagePreview = reader.result as string;
			};
			reader.readAsDataURL(file);
		}
	}

	function removeImage() {
		imageFile = null;
		imagePreview = null;
		if (fileInputEl) {
			fileInputEl.value = '';
		}
	}

	function handleInput() {
		if (textareaEl) {
			textareaEl.style.height = 'auto';
			textareaEl.style.height = `${textareaEl.scrollHeight}px`;
		}
	}
</script>

<div class="chat-input-container">
	{#if fileError}
		<div class="file-error" role="alert">{fileError}</div>
	{/if}
	{#if imagePreview}
		<div class="image-preview">
			<img src={imagePreview} alt="Upload preview" />
			<button
				class="remove-image"
				onclick={removeImage}
				aria-label="Remove image"
			>
				&times;
			</button>
		</div>
	{/if}

	<div class="input-row">
		<button
			class="upload-button"
			onclick={() => fileInputEl?.click()}
			disabled={isLoading}
			aria-label="Upload image"
		>
			<svg
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"
				/>
			</svg>
		</button>

		<input
			bind:this={fileInputEl}
			type="file"
			accept="image/*"
			onchange={handleFileSelect}
			class="file-input-hidden"
			aria-label="Upload image file"
		/>

		<textarea
			bind:this={textareaEl}
			bind:value={text}
			placeholder="Describe an image to generate, or upload an image to edit..."
			aria-label="Message input"
			rows="1"
			disabled={isLoading}
			onkeydown={handleKeyDown}
			oninput={handleInput}
		></textarea>

		<button
			class="send-button"
			onclick={handleSend}
			disabled={!canSend}
			aria-label="Send message"
		>
			<svg
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<line x1="22" y1="2" x2="11" y2="13" />
				<polygon points="22 2 15 22 11 13 2 9 22 2" />
			</svg>
		</button>
	</div>
</div>

<style>
	.chat-input-container {
		padding: 12px 16px;
		background-color: #1a1a2e;
		border-top: 1px solid #333;
	}

	.file-error {
		color: #e94560;
		font-size: 13px;
		margin-bottom: 8px;
	}

	.image-preview {
		position: relative;
		display: inline-block;
		margin-bottom: 8px;
	}

	.image-preview img {
		max-height: 80px;
		border-radius: 8px;
	}

	.remove-image {
		position: absolute;
		top: -6px;
		right: -6px;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		border: none;
		background: #e94560;
		color: white;
		font-size: 14px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		line-height: 1;
	}

	.input-row {
		display: flex;
		align-items: flex-end;
		gap: 8px;
	}

	.upload-button,
	.send-button {
		flex-shrink: 0;
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #eee;
	}

	.upload-button {
		background-color: #16213e;
	}

	.upload-button:hover:not(:disabled) {
		background-color: #0f3460;
	}

	.send-button {
		background-color: #e94560;
	}

	.send-button:hover:not(:disabled) {
		background-color: #d63851;
	}

	.send-button:disabled,
	.upload-button:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.file-input-hidden {
		display: none;
	}

	textarea {
		flex: 1;
		resize: none;
		border: 1px solid #333;
		border-radius: 12px;
		padding: 10px 14px;
		font-size: 14px;
		line-height: 1.5;
		max-height: 150px;
		overflow-y: auto;
		background-color: #16213e;
		color: #eee;
		font-family: inherit;
	}

	textarea::placeholder {
		color: #888;
	}

	textarea:focus {
		outline: none;
		border-color: #e94560;
	}

	textarea:disabled {
		opacity: 0.6;
	}
</style>
