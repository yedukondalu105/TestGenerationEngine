import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch("http://127.0.0.1:8000/api/download-zip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Download failed" }));
    return NextResponse.json(err, { status: res.status });
  }

  const blob = await res.blob();
  const filename =
    res.headers.get("Content-Disposition")?.match(/filename="(.+?)"/)?.[1] ??
    "test_cases.zip";

  return new NextResponse(blob, {
    status: 200,
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}
