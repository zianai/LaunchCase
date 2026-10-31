import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "LaunchCase · 产品开发工作台",
  description: "从证据到产品决策，保持每一步可追溯。",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
