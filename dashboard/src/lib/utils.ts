import camelcaseKeys from 'camelcase-keys';
import { clsx, type ClassValue } from 'clsx';
import ky from 'ky';
import snakecaseKeys from 'snakecase-keys';
import { twMerge } from 'tailwind-merge';

// API client with automatic camelCase/snake_case conversion
export const api = ky.create({
	hooks: {
		beforeRequest: [
			async ({ request }) => {
				if (request.body && request.headers.get('content-type')?.includes('application/json')) {
					const originalJson = await request.clone().json();
					if (typeof originalJson !== 'object' || originalJson === null) {
						return request; // Only transform if it's a JSON object
					}
					const snakeJson = snakecaseKeys(originalJson, { deep: true });
					return new Request(request, { body: JSON.stringify(snakeJson) });
				}
			}
		],
		afterResponse: [
			async ({ response }) => {
				if (response.headers.get('content-type')?.includes('application/json')) {
					const originalJson = (await response.json()) as Record<string, unknown>;
					if (typeof originalJson !== 'object' || originalJson === null) {
						return response; // Only transform if it's a JSON object
					}
					const camelJson = camelcaseKeys(originalJson, { deep: true });
					const headers = new Headers(response.headers);
					headers.delete('content-length');
					return new Response(JSON.stringify(camelJson), {
						status: response.status,
						statusText: response.statusText,
						headers
					});
				}
			}
		]
	}
});

// Installed by shadcn-svelte
// ---------------------------------------------------------------------------------------
export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, 'child'> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, 'children'> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };
