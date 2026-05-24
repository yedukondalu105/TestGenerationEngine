import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300;

export async function POST(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/test-suites/${params.id}/run`, {
      method: "POST",
    });
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
  } catch (e) {
    return NextResponse.json({ detail: `Backend unreachable: ${e}` }, { status: 502 });
  }
}
