// This runs on the server side for every page load
export function load({ url }: { url: URL }) {
  return {
    url: url.pathname,
  };
}
