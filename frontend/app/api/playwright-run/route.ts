import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300; // 5 minutes — covers codegen + test execution

export async function POST(req: NextRequest) {
  const body = await req.json();

  let res: Response;
  try {
    res = await fetch("http://127.0.0.1:8000/api/playwright-run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    return NextResponse.json({ detail: `Backend unreachable: ${e}` }, { status: 502 });
  }

  let data: unknown;
  try {
    data = await res.json();
  } catch {
    const text = await res.text().catch(() => "(no body)");
    return NextResponse.json({ detail: `Backend returned non-JSON (${res.status}): ${text.slice(0, 500)}` }, { status: res.status });
  }

  if (!res.ok) {
    return NextResponse.json(data, { status: res.status });
  }

  return NextResponse.json(data);
}
