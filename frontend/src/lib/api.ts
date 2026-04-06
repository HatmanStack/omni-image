import { API_URL } from './config';
import type { ChatRequest, ChatResponse, UsageResponse } from './types';

const CHAT_TIMEOUT_MS = 125_000;

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
	const controller = new AbortController();
	const timeout = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);

	let response: Response;
	try {
		response = await fetch(`${API_URL}/api/chat`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(request),
			signal: controller.signal
		});
	} catch (err) {
		if (err instanceof DOMException && err.name === 'AbortError') {
			throw new Error('Request timed out');
		}
		throw new Error('Network error: unable to reach the server');
	} finally {
		clearTimeout(timeout);
	}

	if (!response.ok) {
		const data = await response
			.json()
			.catch(() => ({ error: 'Unknown error' }));
		throw new Error(
			data.error || `Request failed with status ${response.status}`
		);
	}

	return response.json();
}

export async function getUsage(): Promise<UsageResponse> {
	let response: Response;
	try {
		response = await fetch(`${API_URL}/api/usage`);
	} catch {
		throw new Error('Network error: unable to reach the server');
	}

	if (!response.ok) {
		throw new Error(`Failed to fetch usage: ${response.status}`);
	}

	return response.json();
}

export async function getHealth(): Promise<{
	status: string;
	model: string;
	region: string;
}> {
	let response: Response;
	try {
		response = await fetch(`${API_URL}/api/health`);
	} catch {
		throw new Error('Network error: unable to reach the server');
	}

	if (!response.ok) {
		throw new Error(`Failed to fetch health: ${response.status}`);
	}

	return response.json();
}
