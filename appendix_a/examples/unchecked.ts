// Deliberate type error: Node strips annotations but does not type-check.
const maxSteps: number = "3";
console.log(maxSteps + 1);
