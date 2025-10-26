import { browser } from '$app/environment';
import { auth } from '$lib/stores/auth';
import { redirect } from '@sveltejs/kit';
import { get } from 'svelte/store';

// Client-side route protection
export async function load({ url, route }: { url: URL; route: { id: string | null } }) {
  // Only run on client side
  if (browser) {
    const { isAuthenticated } = get(auth);
    
    // Redirect to login if not authenticated and not on login page
    if (!isAuthenticated && !route.id?.includes('login')) {
      throw redirect(307, `/login?redirect=${encodeURIComponent(url.pathname)}`);
    }
    
    // Redirect to home if authenticated and on login page
    if (isAuthenticated && route.id?.includes('login')) {
      throw redirect(307, '/');
    }
  }
  
  return {};
};
