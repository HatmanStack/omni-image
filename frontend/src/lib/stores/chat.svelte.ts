/* eslint-disable svelte/prefer-svelte-reactivity */
import { sendChat } from '$lib/api';
import type {
	ChatMessage,
	ChatRequest,
	InferenceConfig,
	Message,
	ContentBlock
} from '$lib/types';

const MIME_TO_FORMAT: Record<string, string> = {
	'image/jpeg': 'jpeg',
	'image/jpg': 'jpeg',
	'image/png': 'png',
	'image/gif': 'gif',
	'image/webp': 'webp'
};

export function fileToBase64(file: File): Promise<string> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => {
			const result = reader.result as string;
			// Remove the data URL prefix (e.g., "data:image/png;base64,")
			const base64 = result.includes(',') ? result.split(',')[1] : result;
			resolve(base64);
		};
		reader.onerror = () => reject(new Error('Failed to read file'));
		reader.readAsDataURL(file);
	});
}

export function chatMessagesToApiMessages(messages: ChatMessage[]): Message[] {
	return messages
		.filter((m) => !m.isLoading)
		.map((m) => {
			const content: ContentBlock[] = [];
			if (m.image && m.role === 'user') {
				content.push({
					image: {
						format: m.imageFormat || 'png',
						data: m.image
					}
				});
			}
			if (m.text) {
				content.push({ text: m.text });
			}
			return { role: m.role, content };
		});
}

function generateId(): string {
	return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function createChatStore() {
	let messages = $state<ChatMessage[]>([]);
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let settings = $state<InferenceConfig>({});

	const hasMessages = $derived(messages.length > 0);
	const lastMessage = $derived(messages[messages.length - 1]);

	async function sendMessage(text: string, imageFile?: File): Promise<void> {
		const userMessage: ChatMessage = {
			id: generateId(),
			role: 'user',
			text,
			timestamp: new Date()
		};

		isLoading = true;
		error = null;

		let loadingMessageId: string | null = null;

		try {
			if (imageFile) {
				const fmt = MIME_TO_FORMAT[imageFile.type];
				if (!fmt) {
					throw new Error(
						`Unsupported image type: ${imageFile.type || 'unknown'}. Use PNG, JPEG, GIF, or WebP.`
					);
				}
				userMessage.image = await fileToBase64(imageFile);
				userMessage.imageFormat = fmt;
			}

			messages.push(userMessage);

			const loadingMessage: ChatMessage = {
				id: generateId(),
				role: 'assistant',
				isLoading: true,
				timestamp: new Date()
			};
			loadingMessageId = loadingMessage.id;
			messages.push(loadingMessage);

			const apiMessages = chatMessagesToApiMessages(messages);
			const request: ChatRequest = { messages: apiMessages };
			if (Object.keys(settings).length > 0) {
				request.inferenceConfig = { ...settings };
			}

			const response = await sendChat(request);

			const loadingIndex = messages.findIndex((m) => m.id === loadingMessageId);
			if (loadingIndex !== -1) {
				messages[loadingIndex] = {
					id: loadingMessageId,
					role: 'assistant',
					text: response.text || undefined,
					image: response.image || undefined,
					imageFormat: response.image_format || 'png',
					timestamp: new Date(),
					isLoading: false
				};
			}
		} catch (err) {
			// Remove loading placeholder and failed user message
			const idsToRemove = new Set<string>([userMessage.id]);
			if (loadingMessageId) {
				idsToRemove.add(loadingMessageId);
			}
			messages = messages.filter((m) => !idsToRemove.has(m.id));
			const errorMessage = err instanceof Error ? err.message : 'Unknown error';
			if (errorMessage.toLowerCase().includes('rate limit')) {
				error = 'Rate limit reached. Please wait before sending more requests.';
			} else if (errorMessage.toLowerCase().includes('network error')) {
				error = 'Unable to reach the server. Please check your connection.';
			} else if (errorMessage.toLowerCase().includes('timed out')) {
				error = 'Request timed out. Please try again.';
			} else if (
				errorMessage.startsWith('Unsupported image type') ||
				errorMessage.startsWith('File too large')
			) {
				error = errorMessage;
			} else {
				error = 'Something went wrong. Please try again.';
			}
		} finally {
			isLoading = false;
		}
	}

	function clearMessages(): void {
		messages = [];
	}

	function clearError(): void {
		error = null;
	}

	function updateSettings(config: Partial<InferenceConfig>): void {
		settings = { ...settings, ...config };
	}

	return {
		get messages() {
			return messages;
		},
		get isLoading() {
			return isLoading;
		},
		get error() {
			return error;
		},
		get settings() {
			return settings;
		},
		get hasMessages() {
			return hasMessages;
		},
		get lastMessage() {
			return lastMessage;
		},
		sendMessage,
		clearMessages,
		clearError,
		updateSettings
	};
}
