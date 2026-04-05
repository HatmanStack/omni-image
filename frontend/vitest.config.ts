import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [svelte({ hot: !process.env.VITEST })],
	test: {
		environment: 'jsdom',
		include: ['src/**/*.test.ts'],
		globals: true
	},
	resolve: {
		conditions: ['browser'],
		alias: {
			$lib: '/src/lib'
		}
	}
});
