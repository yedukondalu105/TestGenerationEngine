import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backendFetch";

export const maxDuration = 300;

export async function POST(req: NextRequest) {
  const body = await req.text();

  try {
    const { status, data } = await backendFetch(
      "http://127.0.0.1:8000/api/playwright-generate",
      "POST",
      body,
    );
    return NextResponse.json(data, { status });
  } catch (e) {
    return NextResponse.json({ detail: `Backend unreachable: ${e}` }, { status: 502 });
  }
}
