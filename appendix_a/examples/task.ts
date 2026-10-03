type Task = { goal: string; maxSteps: number };

function describe(task: Task): string {
  return task.goal + "，最多 " + task.maxSteps + " 步";
}

const task: Task = { goal: "检查链接", maxSteps: 3 };
console.log(describe(task));
