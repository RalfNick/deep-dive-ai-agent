import test from "node:test";
import assert from "node:assert/strict";

import { assertMathAudit, offlineMathJaxOptions } from "../render_checks.mjs";

test("disables MathJax features that fetch SRE assets under file URLs", () => {
  assert.deepEqual(offlineMathJaxOptions, {
    enableMenu: false,
    enableEnrichment: false,
    enableSpeech: false,
    enableBraille: false,
    menuOptions: {
      settings: {
        enrich: false,
        speech: false,
        braille: false,
      },
    },
  });
});

test("accepts a complete local MathJax render", () => {
  assert.doesNotThrow(() =>
    assertMathAudit({
      expected: 3,
      rendered: 3,
      rawWrappers: 0,
      pageErrors: [],
      failedRequests: [],
    }),
  );
});

test("rejects missing formulas instead of silently publishing raw LaTeX", () => {
  assert.throws(
    () =>
      assertMathAudit({
        expected: 3,
        rendered: 2,
        rawWrappers: 1,
        pageErrors: [],
        failedRequests: [],
      }),
    /Math rendering audit failed/,
  );
});

test("rejects browser and asset loading failures", () => {
  assert.throws(
    () =>
      assertMathAudit({
        expected: 1,
        rendered: 1,
        rawWrappers: 0,
        pageErrors: ["MathJax startup failed"],
        failedRequests: ["file:" + "///missing/font.woff2"],
      }),
    /Math rendering audit failed/,
  );
});
