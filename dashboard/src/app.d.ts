// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		interface Platform {
			env?: {
				HOST_CLUSTER_URL: string;
				HOST_GATEWAY_URL: string;
				RECOMPUTATION_CLUSTER_URL: string;
			};
		}
	}
}

export {};
