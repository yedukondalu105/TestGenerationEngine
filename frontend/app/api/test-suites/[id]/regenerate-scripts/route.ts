import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const segments = req.nextUrl.pathname.split("/");
  const id = segments[segments.length - 2]; // .../[id]/regenerate-scripts
  const body = await req.json();
  const res = await fetch(`http://127.0.0.1:8000/api/test-suites/${id}/regenerate-scripts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
