import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import Page from './+page.svelte';

vi.mock('$lib/api', () => ({
	sendChat: vi.fn()
}));

describe('+page.svelte', () => {
	it('shows example prompts on initial render', () => {
		render(Page);
		expect(screen.getByText('Try an example')).toBeTruthy();
	});

	it('shows error banner when error is present', async () => {
		const { sendChat } = await import('$lib/api');
		vi.mocked(sendChat).mockRejectedValueOnce(new Error('Test error'));

		render(Page);

		// Type into textarea and send
		const textarea = screen.getByPlaceholderText(
			'Describe an image to generate, or upload an image to edit...'
		);
		await fireEvent.input(textarea, { target: { value: 'Test prompt' } });
		const sendButton = screen.getByLabelText('Send message');
		await fireEvent.click(sendButton);

		// Wait for the error to appear
		await vi.waitFor(() => {
			expect(screen.getByText('Test error')).toBeTruthy();
		});
	});

	it('error banner dismiss clears error', async () => {
		const { sendChat } = await import('$lib/api');
		vi.mocked(sendChat).mockRejectedValueOnce(new Error('Dismissable error'));

		render(Page);

		const textarea = screen.getByPlaceholderText(
			'Describe an image to generate, or upload an image to edit...'
		);
		await fireEvent.input(textarea, { target: { value: 'Test' } });
		const sendButton = screen.getByLabelText('Send message');
		await fireEvent.click(sendButton);

		await vi.waitFor(() => {
			expect(screen.getByText('Dismissable error')).toBeTruthy();
		});

		const dismissButton = screen.getByLabelText('Dismiss error');
		await fireEvent.click(dismissButton);

		expect(screen.queryByText('Dismissable error')).toBeNull();
	});
});
