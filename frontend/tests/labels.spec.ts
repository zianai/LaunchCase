import { test, expect } from "@playwright/test";
import { qaResult } from "../app/labels";

test("QA reads as passed only on an explicit pass with nothing outstanding", () => {
  expect(qaResult({ status: "pass", checks: [], issues: [] }).label).toBe(
    "检查通过",
  );
  for (const qa of [
    { status: "warn", checks: [], issues: [] },
    { status: "warn" },
    { status: "unknown" },
    {},
    undefined,
  ])
    expect(qaResult(qa).label).toBe("检查信息不完整");
  const mock = qaResult({
    status: "warn",
    checks: [],
    issues: [
      { description: "Fixed offline fixture; no semantic image validation" },
    ],
  });
  expect(mock.label).toBe("有待确认项");
  expect(mock.detail).toContain("没有检查画面内容");
  for (const qa of [
    { status: "block" },
    { status: "warn", checks: [{ status: "block" }] },
    { status: "pass", issues: [{ severity: "block", description: "bad" }] },
  ])
    expect(qaResult(qa).label).toBe("阻止使用");
  expect(
    qaResult({ status: "pass", issues: [{ description: "check this" }] }).label,
  ).toBe("有待确认项");
});
