<script lang="ts">
  import '../app.css';
  import favicon from '$lib/assets/favicon.svg';
  import Nav from '$lib/components/Nav.svelte';
  import { page } from '$app/stores';
  import { auth } from '$lib/stores/auth';

  const { data, children } = $props();
</script>

<svelte:head>
  <title>My App</title>
  <meta name="description" content="My App Description" />
  <link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen bg-gray-100">
  {#if $auth.isAuthenticated || $page.url.pathname === '/login'}
    <Nav />
  {/if}
  
  <main class="py-10">
    <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
      <div class="px-4 py-8 sm:px-0">
        {@render children?.()}
      </div>
    </div>
  </main>
</div>
