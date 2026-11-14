import { NextRequest } from "next/server";
export const runtime = "nodejs";

async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const route = path.join("/");
  if (!/^(targets|discovery-sessions)(\/[a-f0-9-]{36}(\/(cancel|events|evidence\/(operations|observations|transitions|relationships)|artifacts\/(openapi|sdk|tests|validation|report)))?)?$/.test(route)) {
    return Response.json({ detail: "Unsupported route" }, { status: 404 });
  }
  const base = process.env.BACKEND_URL;
  const token = process.env.BACKEND_API_TOKEN;
  if (!base || !token) return Response.json({ detail: "Backend is not configured" }, { status: 503 });
  const body = request.method === "POST" ? await request.text() : undefined;
  if (body && body.length > 2048) return Response.json({ detail: "Request too large" }, { status: 413 });
  try {
    const result = await fetch(`${base}/api/v1/${route}`, {
      method: request.method, headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(10000),
    });
    const headers = new Headers({ "Content-Type": result.headers.get("content-type") ?? "application/json", "Cache-Control": "no-store" });
    const filename = result.headers.get("content-disposition");
    if (filename) headers.set("Content-Disposition", filename);
    return new Response(result.body, { status: result.status, headers });
  } catch {
    return Response.json({ detail: "Backend connection failed" }, { status: 502 });
  }
}
export const GET = forward;
export const POST = forward;
