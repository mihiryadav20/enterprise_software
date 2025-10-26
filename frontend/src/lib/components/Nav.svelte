<script lang="ts">
  import { auth } from '$lib/stores/auth';
  import { goto } from '$app/navigation';
  
  function handleLogout() {
    auth.logout();
    goto('/login');
  }
</script>

<nav class="bg-white shadow-sm">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between h-16">
      <div class="flex">
        <div class="flex-shrink-0 flex items-center">
          <h1 class="text-xl font-bold text-gray-900">My App</h1>
        </div>
      </div>
      <div class="flex items-center">
        {#if $auth.isAuthenticated}
          <div class="ml-4 flex items-center md:ml-6">
            <span class="text-sm font-medium text-gray-500 mr-4">
              Welcome, {$auth.user?.username}
            </span>
            <button
              on:click={handleLogout}
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Sign out
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
</nav>
