import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import SettingsPanel from './SettingsPanel.svelte';

describe('SettingsPanel', () => {
	it('panel is initially collapsed', () => {
		render(SettingsPanel, {
			props: { settings: {}, onChange: vi.fn() }
		});

		// The settings controls should not be visible
		expect(screen.queryByText('Temperature')).toBeNull();
	});

	it('clicking gear icon opens panel', async () => {
		render(SettingsPanel, {
			props: { settings: {}, onChange: vi.fn() }
		});

		const toggleButton = screen.getByLabelText('Toggle settings');
		await fireEvent.click(toggleButton);

		expect(screen.getByText('Temperature')).toBeTruthy();
		expect(screen.getByText('Max Tokens')).toBeTruthy();
		expect(screen.getByText('Top P')).toBeTruthy();
		expect(screen.getByText('Top K')).toBeTruthy();
	});

	it('temperature slider updates value', async () => {
		const onChange = vi.fn();
		render(SettingsPanel, {
			props: { settings: {}, onChange }
		});

		const toggleButton = screen.getByLabelText('Toggle settings');
		await fireEvent.click(toggleButton);

		const tempSlider = screen.getByLabelText('Temperature');
		await fireEvent.input(tempSlider, { target: { value: '0.5' } });

		expect(onChange).toHaveBeenCalledWith(
			expect.objectContaining({ temperature: 0.5 })
		);
	});

	it('reset button clears a setting', async () => {
		const onChange = vi.fn();
		render(SettingsPanel, {
			props: { settings: { temperature: 0.7 }, onChange }
		});

		const toggleButton = screen.getByLabelText('Toggle settings');
		await fireEvent.click(toggleButton);

		const resetButtons = screen.getAllByLabelText(/Reset/);
		// Click the reset for temperature (first slider reset)
		await fireEvent.click(resetButtons[0]);

		expect(onChange).toHaveBeenCalled();
	});
});
