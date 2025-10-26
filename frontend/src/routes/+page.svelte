<script lang="ts">
  import { page } from '$app/stores';
  import { auth } from '$lib/stores/auth';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  // Redirect to login if not authenticated
  onMount(() => {
    if (!$auth.isAuthenticated) {
      goto('/login');
    }
  });
</script>

<div class="max-w-4xl mx-auto px-4 py-8">
  {#if $auth.isAuthenticated}
    <div class="bg-white shadow rounded-lg p-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-4">Welcome, {$auth.user?.username}!</h1>
      <p class="text-gray-600 mb-6">You have successfully logged in to the application.</p>
      
      <div class="bg-gray-50 p-4 rounded-md">
        <h2 class="text-lg font-medium text-gray-900 mb-2">Your Session</h2>
        <div class="space-y-2 text-sm text-gray-600">
          <div class="flex">
            <span class="w-32 font-medium">Username:</span>
            <span>{$auth.user?.username}</span>
          </div>
          <div class="flex">
            <span class="w-32 font-medium">Session Active:</span>
            <span class="text-green-600">Active</span>
          </div>
        </div>
      </div>

      <div class="mt-8">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <a 
            href="/profile" 
            class="bg-white border border-gray-300 rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <h3 class="font-medium text-gray-900">View Profile</h3>
            <p class="text-sm text-gray-500 mt-1">Update your account information</p>
          </a>
          <a 
            href="/settings" 
            class="bg-white border border-gray-300 rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <h3 class="font-medium text-gray-900">Settings</h3>
            <p class="text-sm text-gray-500 mt-1">Configure your preferences</p>
          </a>
        </div>
      </div>
    </div>
  {/if}
</div>
