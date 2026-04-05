import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import ChatMessage from './ChatMessage.svelte';
import type { ChatMessage as ChatMessageType } from '$lib/types';

describe('ChatMessage', () => {
	it('renders user text message', () => {
		const message: ChatMessageType = {
			id: '1',
			role: 'user',
			text: 'Generate a cat',
			timestamp: new Date()
		};

		render(ChatMessage, { props: { message } });
		expect(screen.getByText('Generate a cat')).toBeTruthy();
	});

	it('renders user message with image', () => {
		const message: ChatMessageType = {
			id: '2',
			role: 'user',
			text: 'Edit this image',
			image: 'dGVzdA==',
			imageFormat: 'png',
			timestamp: new Date()
		};

		render(ChatMessage, { props: { message } });
		expect(screen.getByText('Edit this image')).toBeTruthy();
		const img = screen.getByRole('img');
		expect(img).toBeTruthy();
	});

	it('renders assistant text message', () => {
		const message: ChatMessageType = {
			id: '3',
			role: 'assistant',
			text: 'Here is your response',
			timestamp: new Date()
		};

		render(ChatMessage, { props: { message } });
		expect(screen.getByText('Here is your response')).toBeTruthy();
	});

	it('renders assistant image and text message', () => {
		const message: ChatMessageType = {
			id: '4',
			role: 'assistant',
			text: 'Here is your cat',
			image: 'dGVzdA==',
			imageFormat: 'png',
			timestamp: new Date()
		};

		render(ChatMessage, { props: { message } });
		expect(screen.getByText('Here is your cat')).toBeTruthy();
		const img = screen.getByRole('img');
		expect(img).toBeTruthy();
	});

	it('renders loading indicator', () => {
		const message: ChatMessageType = {
			id: '5',
			role: 'assistant',
			isLoading: true,
			timestamp: new Date()
		};

		render(ChatMessage, { props: { message } });
		expect(screen.getByLabelText('Loading response')).toBeTruthy();
	});
});
