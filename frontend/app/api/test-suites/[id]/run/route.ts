import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300;

export async function POST(req: NextRequest) {
  // Extract suite id from URL path: /api/test-suites/{id}/run
  const segments = req.nextUrl.pathname.split("/");
  const id = segments[segments.length - 2];

  let res: Response;
  try {
    res = await fetch(`http://127.0.0.1:8000/api/test-suites/${id}/run`, {
      method: "POST",
    });
  } catch (e) {
    return NextResponse.json({ detail: `Backend unreachable: ${e}` }, { status: 502 });
  }

  let data: unknown;
  try {
    data = await res.json();
  } catch {
    const text = await res.text().catch(() => "(no body)");
    return NextResponse.json(
      { detail: `Backend error (${res.status}): ${text.slice(0, 500)}` },
      { status: res.status }
    );
  }

  if (!res.ok) return NextResponse.json(data, { status: res.status });
  return NextResponse.json(data);
}
