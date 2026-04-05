import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
	createChatStore,
	chatMessagesToApiMessages,
	fileToBase64
} from './chat.svelte';

vi.mock('$lib/api', () => ({
	sendChat: vi.fn()
}));

import { sendChat } from '$lib/api';

const mockSendChat = vi.mocked(sendChat);

beforeEach(() => {
	mockSendChat.mockReset();
});

describe('createChatStore', () => {
	it('initializes with empty state', () => {
		const store = createChatStore();
		expect(store.messages).toEqual([]);
		expect(store.isLoading).toBe(false);
		expect(store.error).toBeNull();
		expect(store.hasMessages).toBe(false);
	});

	it('sendMessage adds user message and calls API', async () => {
		mockSendChat.mockResolvedValueOnce({
			text: 'Here is your image',
			image: 'base64imagedata',
			usage: null,
			latency_ms: 100
		});

		const store = createChatStore();
		await store.sendMessage('Generate a cat');

		expect(store.messages).toHaveLength(2);
		expect(store.messages[0].role).toBe('user');
		expect(store.messages[0].text).toBe('Generate a cat');
		expect(store.messages[1].role).toBe('assistant');
		expect(store.messages[1].text).toBe('Here is your image');
		expect(store.messages[1].image).toBe('base64imagedata');
		expect(store.isLoading).toBe(false);
		expect(mockSendChat).toHaveBeenCalledOnce();
	});

	it('sendMessage handles errors', async () => {
		mockSendChat.mockRejectedValueOnce(new Error('Something went wrong'));

		const store = createChatStore();
		await store.sendMessage('Generate a cat');

		expect(store.messages).toHaveLength(1);
		expect(store.messages[0].role).toBe('user');
		expect(store.error).toBe('Something went wrong');
		expect(store.isLoading).toBe(false);
	});

	it('sendMessage shows rate limit friendly message', async () => {
		const error = new Error('Rate limit exceeded');
		mockSendChat.mockRejectedValueOnce(error);

		const store = createChatStore();
		await store.sendMessage('Generate a cat');

		expect(store.error).toContain('Rate limit');
	});

	it('clearMessages resets messages', async () => {
		mockSendChat.mockResolvedValueOnce({
			text: 'Response',
			image: null,
			usage: null,
			latency_ms: 100
		});

		const store = createChatStore();
		await store.sendMessage('test');
		expect(store.messages.length).toBeGreaterThan(0);

		store.clearMessages();
		expect(store.messages).toEqual([]);
	});

	it('updateSettings updates inference config', () => {
		const store = createChatStore();
		store.updateSettings({ temperature: 0.5 });
		expect(store.settings.temperature).toBe(0.5);

		store.updateSettings({ topP: 0.9 });
		expect(store.settings.temperature).toBe(0.5);
		expect(store.settings.topP).toBe(0.9);
	});

	it('clearError sets error to null', async () => {
		mockSendChat.mockRejectedValueOnce(new Error('fail'));

		const store = createChatStore();
		await store.sendMessage('test');
		expect(store.error).not.toBeNull();

		store.clearError();
		expect(store.error).toBeNull();
	});

	it('sendMessage passes settings as inferenceConfig', async () => {
		mockSendChat.mockResolvedValueOnce({
			text: 'ok',
			image: null,
			usage: null,
			latency_ms: 50
		});

		const store = createChatStore();
		store.updateSettings({ temperature: 0.7 });
		await store.sendMessage('test');

		expect(mockSendChat).toHaveBeenCalledWith(
			expect.objectContaining({
				inferenceConfig: { temperature: 0.7 }
			})
		);
	});
});

describe('chatMessagesToApiMessages', () => {
	it('converts ChatMessage array to Message array', () => {
		const chatMessages = [
			{
				id: '1',
				role: 'user' as const,
				text: 'Hello',
				timestamp: new Date()
			},
			{
				id: '2',
				role: 'assistant' as const,
				text: 'Hi there',
				image: 'base64data',
				imageFormat: 'png',
				timestamp: new Date()
			}
		];

		const result = chatMessagesToApiMessages(chatMessages);
		expect(result).toHaveLength(2);
		expect(result[0]).toEqual({
			role: 'user',
			content: [{ type: 'text', text: 'Hello' }]
		});
		expect(result[1].content).toHaveLength(2);
		expect(result[1].content[0]).toEqual({
			image: {
				format: 'png',
				data: 'base64data'
			}
		});
		expect(result[1].content[1]).toEqual({ type: 'text', text: 'Hi there' });
	});

	it('excludes loading messages', () => {
		const chatMessages = [
			{ id: '1', role: 'user' as const, text: 'Hello', timestamp: new Date() },
			{
				id: '2',
				role: 'assistant' as const,
				isLoading: true,
				timestamp: new Date()
			}
		];

		const result = chatMessagesToApiMessages(chatMessages);
		expect(result).toHaveLength(1);
	});
});

describe('fileToBase64', () => {
	it('converts a file to base64 string', async () => {
		const content = 'hello';
		const file = new File([content], 'test.txt', { type: 'text/plain' });

		const result = await fileToBase64(file);
		expect(typeof result).toBe('string');
		expect(result.length).toBeGreaterThan(0);
	});
});
