export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

/**
 * Robust fetch helper with dual-host fallback (127.0.0.1 <-> localhost).
 */
export async function safeFetch(url: string, options?: RequestInit): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem("tradegod_token") : null;
  const headers = new Headers(options?.headers || {});
  
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const mergedOptions = {
    ...options,
    headers
  };

  try {
    const res = await fetch(url, mergedOptions);
    return res;
  } catch (err) {
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
        throw err;
      }
    }
    throw err;
  }
}
