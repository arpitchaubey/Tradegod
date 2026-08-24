export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

/**
 * Robust fetch helper with retry logic for cold-starts and dual-host fallback (127.0.0.1 <-> localhost).
 */
export async function safeFetch(url: string, options?: RequestInit, maxRetries = 3): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem("tradegod_token") : null;
  const headers = new Headers(options?.headers || {});
  
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const mergedOptions = {
    ...options,
    headers
  };

  let lastError: any = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, mergedOptions);
      // If response is 502 or 503 (Render instance spinning up), retry after delay if attempts remain
      if ((res.status === 502 || res.status === 503) && attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 2500));
        continue;
      }
      return res;
    } catch (err) {
      lastError = err;
      
      // Dual-host fallback for local dev
      let fallbackUrl = "";
      if (url.includes("127.0.0.1")) {
        fallbackUrl = url.replace("127.0.0.1", "localhost");
      } else if (url.includes("localhost")) {
        fallbackUrl = url.replace("localhost", "127.0.0.1");
      }

      if (fallbackUrl) {
        try {
          const fallbackRes = await fetch(fallbackUrl, mergedOptions);
          return fallbackRes;
        } catch (e) {
          // ignore fallback error and continue retry loop
        }
      }

      if (attempt < maxRetries) {
        // Wait 2.5s before retrying (Render cold start takes ~20-30s)
        await new Promise((resolve) => setTimeout(resolve, 2500));
      }
    }
  }

  throw lastError || new Error("Failed to connect to backend service");
}
