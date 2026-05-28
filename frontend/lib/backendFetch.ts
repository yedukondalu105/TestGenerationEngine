/**
 * HTTP utility for long-running backend calls.
 * Uses node:http directly to avoid undici's 300-second headersTimeout,
 * which kills proxy fetches for test-run and LLM-generation endpoints.
 */
import { request as httpReq } from "node:http";

export interface BackendResponse {
  status: number;
  data: unknown;
}

export function backendFetch(
  url: string,
  method = "GET",
  body?: string,
): Promise<BackendResponse> {
  return new Promise((resolve, reject) => {
    const headers: Record<string, string | number> = {};
    if (body) {
      headers["Content-Type"] = "application/json";
      headers["Content-Length"] = Buffer.byteLength(body);
    }

    const req = httpReq(url, { method, headers }, (res) => {
      const chunks: Buffer[] = [];
      res.on("data", (c: Buffer) => chunks.push(c));
      res.on("end", () => {
        const raw = Buffer.concat(chunks).toString("utf-8");
        try {
          resolve({ status: res.statusCode ?? 500, data: JSON.parse(raw) });
        } catch {
          reject(new Error(`Non-JSON backend response (${res.statusCode}): ${raw.slice(0, 300)}`));
        }
      });
    });

    req.on("error", reject);
    req.setTimeout(0); // disable socket timeout — backend controls when it responds
    if (body) req.write(body);
    req.end();
  });
}
