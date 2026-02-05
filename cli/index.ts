import readline from "readline";
import { storage } from "../server/storage.js";
import { chat } from "../server/claude.js";
import { initDb } from "../server/db.js";
import { executeCode } from "../server/code-executor.js";

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

async function main() {
  await initDb();

  console.log("\n╔════════════════════════════════╗");
  console.log("║   CLAUDEBOT CLI - GATEWAY      ║");
  console.log("║   v1.0 | OPERATIONAL           ║");
  console.log("╚════════════════════════════════╝\n");

  console.log("Commands:");
  console.log("  /exec <code>   - Execute JavaScript");
  console.log("  /py <code>     - Execute Python");
  console.log("  /help          - Show this help");
  console.log("  /quit          - Exit\n");

  // Create or get conversation
  const convs = await storage.getConversations();
  let conv = convs[0] || (await storage.createConversation("CLI Session"));

  console.log(`Active conversation: ${conv.title}\n`);

  const prompt = () => {
    rl.question("You: ", async (input) => {
      if (input.toLowerCase() === "exit" || input.toLowerCase() === "quit" || input.toLowerCase() === "/quit") {
        console.log("\nGoodbye!");
        rl.close();
        process.exit(0);
      }

      if (input === "/help") {
        console.log("\nCommands:");
        console.log("  /exec <code>   - Execute JavaScript");
        console.log("  /py <code>     - Execute Python");
        console.log("  /help          - Show this help");
        console.log("  /quit          - Exit\n");
        prompt();
        return;
      }

      // Handle code execution
      if (input.startsWith("/exec ")) {
        const code = input.slice(6);
        try {
          const result = await executeCode(code, "javascript");
          if (result.error) {
            console.log(`\n✗ Error: ${result.error}`);
          } else {
            console.log(`\n✓ Output:\n${result.output}\n`);
          }
        } catch (err) {
          console.log(`\n✗ Execution error: ${err}\n`);
        }
        prompt();
        return;
      }

      if (input.startsWith("/py ")) {
        const code = input.slice(4);
        try {
          const result = await executeCode(code, "python");
          if (result.error) {
            console.log(`\n✗ Error: ${result.error}`);
          } else {
            console.log(`\n✓ Output:\n${result.output}\n`);
          }
        } catch (err) {
          console.log(`\n✗ Execution error: ${err}\n`);
        }
        prompt();
        return;
      }

      if (!input.trim()) {
        prompt();
        return;
      }

      // Regular chat
      try {
        // Save user message
        await storage.createMessage(conv.id, "user", input);

        // Get conversation history
        const msgs = await storage.getMessages(conv.id);
        const history = msgs.map((m) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
        }));

        // Get Claude response
        const reply = await chat(history);
        await storage.createMessage(conv.id, "assistant", reply);
        console.log(`\nClaude: ${reply}\n`);
      } catch (err) {
        console.error(`\nError: ${err}\n`);
      }

      prompt();
    });
  };

  prompt();
}

main().catch(console.error);
