/* eslint-disable svelte/prefer-svelte-reactivity */
import { sendChat } from '$lib/api';
import type {
	ChatMessage,
	ChatRequest,
	InferenceConfig,
	Message,
	ContentBlock
} from '$lib/types';

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
			if (m.image) {
				content.push({
					type: 'image',
					format: m.imageFormat || 'png',
					data: m.image
				});
			}
			if (m.text) {
				content.push({ type: 'text', text: m.text });
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

		if (imageFile) {
			userMessage.image = await fileToBase64(imageFile);
			userMessage.imageFormat = imageFile.type.split('/')[1] || 'png';
		}

		messages.push(userMessage);

		const loadingMessage: ChatMessage = {
			id: generateId(),
			role: 'assistant',
			isLoading: true,
			timestamp: new Date()
		};
		messages.push(loadingMessage);

		isLoading = true;
		error = null;

		try {
			const apiMessages = chatMessagesToApiMessages(messages);
			const request: ChatRequest = { messages: apiMessages };
			if (Object.keys(settings).length > 0) {
				request.inferenceConfig = { ...settings };
			}

			const response = await sendChat(request);

			const loadingIndex = messages.findIndex(
				(m) => m.id === loadingMessage.id
			);
			if (loadingIndex !== -1) {
				messages[loadingIndex] = {
					id: loadingMessage.id,
					role: 'assistant',
					text: response.text || undefined,
					image: response.image || undefined,
					imageFormat: 'png',
					timestamp: new Date(),
					isLoading: false
				};
			}
		} catch (err) {
			const loadingIndex = messages.findIndex(
				(m) => m.id === loadingMessage.id
			);
			if (loadingIndex !== -1) {
				messages.splice(loadingIndex, 1);
			}
			const errorMessage = err instanceof Error ? err.message : 'Unknown error';
			if (errorMessage.toLowerCase().includes('rate limit')) {
				error = `Rate limit reached. Please wait before sending more requests.`;
			} else {
				error = errorMessage;
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
