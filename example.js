import AgenticUtility from './agentic-utility.js';

// Example usage with search
const agent = new AgenticUtility();

const config = {
  systemMessage: "You are a market research analyst with expertise in competitive analysis.",
  prompt: "Research and analyze the competitive landscape for the given companies. Focus on pricing, features, and market positioning.",
  goal: "Create a competitive analysis report with recommendations",
  enableSearch: true,
  input: {
    searchQuery: "Notion vs Obsidian vs Roam Research pricing comparison 2025",
    companies: ["Notion", "Obsidian", "Roam Research"],
    focus_areas: ["pricing", "collaboration features", "target audience"],
    format: "structured_report"
  }
};

console.log("🚀 Starting agentic task with search capabilities...");

agent.executeTask(config)
  .then(result => {
    console.log("✅ Task completed!");
    console.log("Result:", result.result);
    console.log("\n📊 Usage:", result.usage);
    if (result.searchResults) {
      console.log("\n🔍 Search performed:", result.searchResults.length, "results found");
    }
  })
  .catch(error => {
    console.error("❌ Error:", error);
  });