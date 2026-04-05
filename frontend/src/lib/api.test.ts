import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sendChat, getUsage, getHealth } from './api';
import type { ChatRequest } from './types';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
	mockFetch.mockReset();
});

describe('sendChat', () => {
	const request: ChatRequest = {
		messages: [{ role: 'user', content: [{ type: 'text', text: 'Generate a cat' }] }]
	};

	it('sends correct request body', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({ text: 'Here is a cat', image: null, usage: null, latency_ms: 100 })
		});

		await sendChat(request);

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/chat'),
			expect.objectContaining({
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(request)
			})
		);
	});

	it('parses successful response', async () => {
		const mockResponse = { text: 'Here is a cat', image: 'base64data', usage: { inputTokens: 10 }, latency_ms: 200 };
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () => Promise.resolve(mockResponse)
		});

		const result = await sendChat(request);
		expect(result).toEqual(mockResponse);
	});

	it('throws on error response', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 429,
			json: () => Promise.resolve({ error: 'Rate limit exceeded', error_code: 'RATE_LIMITED' })
		});

		await expect(sendChat(request)).rejects.toThrow('Rate limit exceeded');
	});

	it('throws on 500 error response', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 500,
			json: () => Promise.resolve({ error: 'Internal server error' })
		});

		await expect(sendChat(request)).rejects.toThrow('Internal server error');
	});

	it('throws on network error', async () => {
		mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

		await expect(sendChat(request)).rejects.toThrow('Network error: unable to reach the server');
	});
});

describe('getUsage', () => {
	it('parses response', async () => {
		const mockResponse = { total_requests: 5, limit: 10, remaining: 5 };
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () => Promise.resolve(mockResponse)
		});

		const result = await getUsage();
		expect(result).toEqual(mockResponse);
	});

	it('throws on error', async () => {
		mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

		await expect(getUsage()).rejects.toThrow('Failed to fetch usage: 500');
	});
});

describe('getHealth', () => {
	it('parses response', async () => {
		const mockResponse = { status: 'healthy', model: 'nova-2-omni', region: 'us-west-2' };
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () => Promise.resolve(mockResponse)
		});

		const result = await getHealth();
		expect(result).toEqual(mockResponse);
	});

	it('throws on error', async () => {
		mockFetch.mockResolvedValueOnce({ ok: false, status: 503 });

		await expect(getHealth()).rejects.toThrow('Failed to fetch health: 503');
	});
});
