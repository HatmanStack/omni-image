export interface TextBlock {
	text: string;
}

export interface ImageBlock {
	image: {
		format: string;
		data: string;
	};
}

export type ContentBlock = TextBlock | ImageBlock;

export interface Message {
	role: 'user' | 'assistant';
	content: ContentBlock[];
}

export interface InferenceConfig {
	maxTokens?: number;
	temperature?: number;
	topP?: number;
	topK?: number;
}

export interface ChatRequest {
	messages: Message[];
	inferenceConfig?: InferenceConfig;
}

export interface ChatResponse {
	text: string | null;
	image: string | null;
	image_format: string | null;
	usage: Record<string, number> | null;
	latency_ms: number | null;
}

export interface ErrorResponse {
	error: string;
	error_code: string;
}

export interface UsageResponse {
	total_requests: number;
	limit: number;
	remaining: number;
}

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	text?: string;
	image?: string;
	imageFormat?: string;
	timestamp: Date;
	isLoading?: boolean;
}
