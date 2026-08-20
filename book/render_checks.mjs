export const offlineMathJaxOptions = Object.freeze({
  enableMenu: false,
  enableEnrichment: false,
  enableSpeech: false,
  enableBraille: false,
  menuOptions: Object.freeze({
    settings: Object.freeze({
      enrich: false,
      speech: false,
      braille: false,
    }),
  }),
});

export function assertMathAudit({
  expected,
  rendered,
  rawWrappers,
  pageErrors = [],
  failedRequests = [],
}) {
  const problems = [];

  if (rendered !== expected) {
    problems.push(`expected ${expected} formulas, rendered ${rendered}`);
  }
  if (rawWrappers !== 0) {
    problems.push(`${rawWrappers} formula wrappers still contain raw LaTeX`);
  }
  if (pageErrors.length > 0) {
    problems.push(`page errors: ${pageErrors.join(" | ")}`);
  }
  if (failedRequests.length > 0) {
    problems.push(`failed requests: ${failedRequests.join(" | ")}`);
  }

  if (problems.length > 0) {
    throw new Error(`Math rendering audit failed: ${problems.join("; ")}`);
  }
}
