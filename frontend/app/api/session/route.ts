import { NextRequest, NextResponse } from "next/server";
export async function POST(request: NextRequest) {
  if (
    request.headers.get("origin") !==
    `${request.nextUrl.protocol}//${request.headers.get("host")}`
  )
    return NextResponse.json(
      { error: { message: "Origin rejected" } },
      { status: 403 },
    );
  const { token } = await request.json();
  if (typeof token !== "string" || token.length > 200)
    return NextResponse.json(
      { error: { message: "Invalid token" } },
      { status: 400 },
    );
  const response = await fetch(
    `${process.env.LAUNCHCASE_API_URL || "http://127.0.0.1:8810"}/api/v1/product-cases`,
    { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" },
  );
  if (!response.ok)
    return NextResponse.json(
      { error: { message: "身份凭证无效" } },
      { status: 401 },
    );
  const result = NextResponse.json({ ok: true });
  result.cookies.set("launchcase_session", token, {
    httpOnly: true,
    sameSite: "strict",
    secure: request.nextUrl.protocol === "https:",
    path: "/",
    maxAge: 28800,
  });
  return result;
}
export async function DELETE(request: NextRequest) {
  if (
    request.headers.get("origin") !==
    `${request.nextUrl.protocol}//${request.headers.get("host")}`
  )
    return NextResponse.json(
      { error: { message: "Origin rejected" } },
      { status: 403 },
    );
  const result = NextResponse.json({ ok: true });
  result.cookies.delete("launchcase_session");
  return result;
}

export async function GET(request: NextRequest) {
  return NextResponse.json(
    { authenticated: !!request.cookies.get("launchcase_session")?.value },
    { headers: { "Cache-Control": "no-store" } },
  );
}
