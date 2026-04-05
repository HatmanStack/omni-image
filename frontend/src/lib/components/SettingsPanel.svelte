<script lang="ts">
	import type { InferenceConfig } from '$lib/types';

	let {
		settings,
		onChange
	}: {
		settings: InferenceConfig;
		onChange: (settings: InferenceConfig) => void;
	} = $props();

	let isOpen = $state(false);

	function updateSetting(
		key: keyof InferenceConfig,
		value: number | undefined
	) {
		const updated = { ...settings, [key]: value };
		if (value === undefined) {
			delete updated[key];
		}
		onChange(updated);
	}

	function handleSliderInput(key: 'temperature' | 'topP', e: Event) {
		const target = e.target as HTMLInputElement;
		updateSetting(key, parseFloat(target.value));
	}

	function handleNumberInput(key: 'maxTokens' | 'topK', e: Event) {
		const target = e.target as HTMLInputElement;
		const val = target.value ? parseInt(target.value, 10) : undefined;
		updateSetting(key, val);
	}

	function resetSetting(key: keyof InferenceConfig) {
		updateSetting(key, undefined);
	}
</script>

<div class="settings-panel">
	<button
		class="toggle-button"
		onclick={() => (isOpen = !isOpen)}
		aria-label="Toggle settings"
	>
		<svg
			width="20"
			height="20"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
		>
			<circle cx="12" cy="12" r="3" />
			<path
				d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
			/>
		</svg>
	</button>

	{#if isOpen}
		<div class="panel-content">
			<div class="setting-row">
				<label for="maxTokens">Max Tokens</label>
				<div class="setting-control">
					<input
						id="maxTokens"
						type="number"
						aria-label="Max Tokens"
						value={settings.maxTokens ?? ''}
						oninput={(e) => handleNumberInput('maxTokens', e)}
						min="1"
						placeholder="Default"
					/>
					<button
						class="reset-btn"
						onclick={() => resetSetting('maxTokens')}
						aria-label="Reset Max Tokens"
					>
						&times;
					</button>
				</div>
			</div>

			<div class="setting-row">
				<label for="temperature">Temperature</label>
				<div class="setting-control">
					<input
						id="temperature"
						type="range"
						aria-label="Temperature"
						value={settings.temperature ?? 0.5}
						oninput={(e) => handleSliderInput('temperature', e)}
						min="0"
						max="1"
						step="0.1"
					/>
					<span class="value-display"
						>{settings.temperature?.toFixed(1) ?? '-'}</span
					>
					<button
						class="reset-btn"
						onclick={() => resetSetting('temperature')}
						aria-label="Reset Temperature"
					>
						&times;
					</button>
				</div>
			</div>

			<div class="setting-row">
				<label for="topP">Top P</label>
				<div class="setting-control">
					<input
						id="topP"
						type="range"
						aria-label="Top P"
						value={settings.topP ?? 0.5}
						oninput={(e) => handleSliderInput('topP', e)}
						min="0"
						max="1"
						step="0.1"
					/>
					<span class="value-display">{settings.topP?.toFixed(1) ?? '-'}</span>
					<button
						class="reset-btn"
						onclick={() => resetSetting('topP')}
						aria-label="Reset Top P"
					>
						&times;
					</button>
				</div>
			</div>

			<div class="setting-row">
				<label for="topK">Top K</label>
				<div class="setting-control">
					<input
						id="topK"
						type="number"
						aria-label="Top K"
						value={settings.topK ?? ''}
						oninput={(e) => handleNumberInput('topK', e)}
						min="1"
						placeholder="Default"
					/>
					<button
						class="reset-btn"
						onclick={() => resetSetting('topK')}
						aria-label="Reset Top K"
					>
						&times;
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.settings-panel {
		position: relative;
	}

	.toggle-button {
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		padding: 8px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: color 0.15s ease;
	}

	.toggle-button:hover {
		color: #eee;
	}

	.panel-content {
		position: absolute;
		right: 0;
		top: 100%;
		background-color: #16213e;
		border: 1px solid #333;
		border-radius: 12px;
		padding: 16px;
		min-width: 280px;
		z-index: 10;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.setting-row {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.setting-row label {
		font-size: 12px;
		color: #888;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.setting-control {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	input[type='range'] {
		flex: 1;
		accent-color: #e94560;
	}

	input[type='number'] {
		flex: 1;
		background-color: #1a1a2e;
		border: 1px solid #333;
		border-radius: 6px;
		color: #eee;
		padding: 6px 8px;
		font-size: 13px;
	}

	input[type='number']::placeholder {
		color: #666;
	}

	.value-display {
		font-size: 13px;
		color: #eee;
		min-width: 24px;
		text-align: center;
	}

	.reset-btn {
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		font-size: 16px;
		padding: 2px 6px;
		border-radius: 4px;
	}

	.reset-btn:hover {
		color: #e94560;
	}
</style>
