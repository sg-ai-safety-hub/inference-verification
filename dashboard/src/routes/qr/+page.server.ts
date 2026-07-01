import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = () => {
	redirect(302, 'https://www.aisafety.sg/blog/making-ai-verification-international');
};
