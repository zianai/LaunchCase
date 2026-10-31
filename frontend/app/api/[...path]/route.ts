import { NextRequest, NextResponse } from "next/server";
async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  if (path.some((p) => !/^[-a-zA-Z0-9_]+$/.test(p)))
    return NextResponse.json(
      { error: { message: "Invalid route" } },
      { status: 400 },
    );
  if (
    !["GET", "HEAD"].includes(request.method) &&
    request.headers.get("origin") !==
      `${request.nextUrl.protocol}//${request.headers.get("host")}`
  )
    return NextResponse.json(
      { error: { message: "Origin rejected" } },
      { status: 403 },
    );
  const token = request.cookies.get("launchcase_session")?.value;
  if (!token)
    return NextResponse.json(
      { error: { message: "请登录本地工作区" } },
      { status: 401 },
    );
  const body = ["GET", "HEAD"].includes(request.method)
    ? undefined
    : await request.text();
  if (body && new TextEncoder().encode(body).length > 1500000)
    return NextResponse.json(
      { error: { message: "文件超过大小限制" } },
      { status: 413 },
    );
  try {
    const upstream = await fetch(
      `${process.env.LAUNCHCASE_API_URL || "http://127.0.0.1:8810"}/api/v1/${path.join("/")}${request.nextUrl.search}`,
      {
        method: request.method,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          "Last-Event-ID": request.headers.get("Last-Event-ID") || "0",
          "Idempotency-Key":
            request.headers.get("Idempotency-Key") || crypto.randomUUID(),
        },
        body,
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(30000),
      },
    );
    const headers = new Headers({
      "Content-Type":
        upstream.headers.get("Content-Type") || "application/json",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    const disposition = upstream.headers.get("Content-Disposition");
    if (disposition) headers.set("Content-Disposition", disposition);
    return new Response(await upstream.arrayBuffer(), {
      status: upstream.status,
      headers,
    });
  } catch {
    return NextResponse.json(
      { error: { message: "无法连接本地 LaunchCase API，请检查服务状态" } },
      { status: 503 },
    );
  }
}
export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
