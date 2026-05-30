import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backendFetch";

export const maxDuration = 120;

export async function POST(req: NextRequest) {
  const segments = req.nextUrl.pathname.split("/");
  const id = segments[segments.length - 2];
  const body = await req.json().catch(() => ({}));

  try {
    const { status, data } = await backendFetch(
      `http://127.0.0.1:8000/api/test-suites/${id}/run-test`,
      "POST",
      JSON.stringify(body),
    );
    return NextResponse.json(data, { status });
  } catch (e) {
    return NextResponse.json({ detail: `Backend unreachable: ${e}` }, { status: 502 });
  }
}
