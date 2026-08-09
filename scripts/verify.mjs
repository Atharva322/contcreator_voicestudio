import { spawnSync } from "node:child_process";

const commands = [
  ["npm", ["run", "test:api"]],
  ["npm", ["run", "typecheck:web"]],
  ["npm", ["run", "build:web"]],
];

for (const [command, args] of commands) {
  const label = [command, ...args].join(" ");
  console.log(`\n> ${label}`);
  const result = spawnSync(command, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
