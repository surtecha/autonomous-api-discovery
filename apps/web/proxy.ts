import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "node:crypto";

export function proxy(request: NextRequest) {
  const username = process.env.WEB_USERNAME;
  const password = process.env.WEB_PASSWORD;
  if (!username || !password || password.length < 16) {
    return new NextResponse("Web authentication is not configured", { status: 503 });
  }
  const expected = Buffer.from("Basic " + Buffer.from(`${username}:${password}`).toString("base64"));
  const actual = Buffer.from(request.headers.get("authorization") ?? "");
  if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) {
    return new NextResponse("Authentication required", { status: 401, headers: { "WWW-Authenticate": 'Basic realm="Discovery workspace"' } });
  }
  const origin = process.env.WEB_ORIGIN ?? "http://127.0.0.1:3000";
  if (!["GET", "HEAD"].includes(request.method) && request.headers.get("origin") !== origin) {
    return new NextResponse("Origin rejected", { status: 403 });
  }
  return NextResponse.next();
}
export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
