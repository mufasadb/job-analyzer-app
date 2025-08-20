import AgenticUtility from './agentic-utility.js';

const agent = new AgenticUtility();
const jobUrl = "https://www.linkedin.com/jobs/view/4286417322";

console.log("🔍 Debugging job content extraction...");

agent.fetchPageContent(jobUrl)
  .then(content => {
    console.log("📄 TITLE:", content.title);
    console.log("\n📋 CONTENT LENGTH:", content.content.length);
    console.log("\n📋 FIRST 500 CHARS:");
    console.log(content.content.substring(0, 500));
    console.log("\n📋 LAST 500 CHARS:");
    console.log(content.content.substring(content.content.length - 500));
  })
  .catch(error => {
    console.error("❌ Error:", error);
  });