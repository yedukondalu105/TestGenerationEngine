import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300; // 5 minutes — covers the full pipeline

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch("http://localhost:8000/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    // Node fetch has no default timeout — request will wait as long as needed
  });

  const data = await res.json();

  if (!res.ok) {
    return NextResponse.json(data, { status: res.status });
  }

  return NextResponse.json(data);
}
