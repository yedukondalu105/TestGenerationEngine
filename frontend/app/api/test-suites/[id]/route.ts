import { NextRequest, NextResponse } from "next/server";

export async function DELETE(req: NextRequest) {
  const segments = req.nextUrl.pathname.split("/");
  const id = segments[segments.length - 1]; // .../[id]
  const res = await fetch(`http://127.0.0.1:8000/api/test-suites/${id}`, { method: "DELETE" });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
