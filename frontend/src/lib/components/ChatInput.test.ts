import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import ChatInput from './ChatInput.svelte';

describe('ChatInput', () => {
	it('renders textarea', () => {
		render(ChatInput, { props: { onSend: vi.fn(), isLoading: false } });
		const textarea = screen.getByPlaceholderText(
			'Describe an image to generate, or upload an image to edit...'
		);
		expect(textarea).toBeTruthy();
	});

	it('send button click calls onSend with text', async () => {
		const onSend = vi.fn();
		render(ChatInput, { props: { onSend, isLoading: false } });

		const textarea = screen.getByPlaceholderText(
			'Describe an image to generate, or upload an image to edit...'
		);
		await fireEvent.input(textarea, { target: { value: 'Generate a cat' } });

		const sendButton = screen.getByLabelText('Send message');
		await fireEvent.click(sendButton);

		expect(onSend).toHaveBeenCalledWith('Generate a cat', undefined);
	});

	it('Enter key calls onSend', async () => {
		const onSend = vi.fn();
		render(ChatInput, { props: { onSend, isLoading: false } });

		const textarea = screen.getByPlaceholderText(
			'Describe an image to generate, or upload an image to edit...'
		);
		await fireEvent.input(textarea, { target: { value: 'Test prompt' } });
		await fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

		expect(onSend).toHaveBeenCalledWith('Test prompt', undefined);
	});

	it('Shift+Enter does not call onSend', async () => {
		const onSend = vi.fn();
		render(ChatInput, { props: { onSend, isLoading: false } });

		const textarea = screen.getByPlaceholderText(
			'Describe an image to generate, or upload an image to edit...'
		);
		await fireEvent.input(textarea, { target: { value: 'Test prompt' } });
		await fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });

		expect(onSend).not.toHaveBeenCalled();
	});

	it('send button is disabled when empty', () => {
		render(ChatInput, { props: { onSend: vi.fn(), isLoading: false } });
		const sendButton = screen.getByLabelText('Send message');
		expect(sendButton.hasAttribute('disabled')).toBe(true);
	});

	it('send button is disabled when loading', async () => {
		render(ChatInput, { props: { onSend: vi.fn(), isLoading: true } });

		const textarea = screen.getByPlaceholderText(
			'Describe an image to generate, or upload an image to edit...'
		);
		await fireEvent.input(textarea, { target: { value: 'Test' } });

		const sendButton = screen.getByLabelText('Send message');
		expect(sendButton.hasAttribute('disabled')).toBe(true);
	});

	it('image file selection shows preview', async () => {
		render(ChatInput, { props: { onSend: vi.fn(), isLoading: false } });

		const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
		expect(fileInput).toBeTruthy();

		const file = new File(['test'], 'test.png', { type: 'image/png' });
		Object.defineProperty(fileInput, 'files', { value: [file] });
		await fireEvent.change(fileInput);

		// After file selection, the remove button should appear (FileReader is async)
		await waitFor(() => {
			const removeButton = screen.queryByLabelText('Remove image');
			expect(removeButton).toBeTruthy();
		});
	});
});
