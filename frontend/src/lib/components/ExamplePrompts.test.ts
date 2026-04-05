import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import ExamplePrompts from './ExamplePrompts.svelte';

const EXPECTED_PROMPTS = [
	'Generate a sunset over mountains with vibrant colors',
	'Create a watercolor painting of a cat reading a book',
	'Design a minimalist logo for a coffee shop',
	'Draw a futuristic cityscape at night'
];

describe('ExamplePrompts', () => {
	it('renders all example prompts', () => {
		render(ExamplePrompts, { props: { onSelect: vi.fn() } });

		for (const prompt of EXPECTED_PROMPTS) {
			expect(screen.getByText(prompt)).toBeTruthy();
		}
	});

	it('clicking a prompt calls onSelect with correct text', async () => {
		const onSelect = vi.fn();
		render(ExamplePrompts, { props: { onSelect } });

		const firstPrompt = screen.getByText(EXPECTED_PROMPTS[0]);
		await fireEvent.click(firstPrompt);

		expect(onSelect).toHaveBeenCalledWith(EXPECTED_PROMPTS[0]);
	});
});
