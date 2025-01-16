// Dark Mode Toggle
const themeToggle = document.getElementById("themeToggle");
const body = document.body;

// Toggle theme on click
themeToggle.addEventListener("click", () => {
  if (body.getAttribute("data-theme") === "dark") {
    body.removeAttribute("data-theme");
  } else {
    body.setAttribute("data-theme", "dark");
  }
});

// Clear Chat
const clearChat = document.getElementById("clearChat");
clearChat.addEventListener("click", () => {
  const chatMessages = document.getElementById("chatMessages");
  chatMessages.innerHTML = ""; // Clear all messages
});

// Handle form submission for search (single listener)
const searchForm = document.getElementById("searchForm");
const userInput = document.getElementById("userInput");

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = userInput.value.trim();
  if (!query) return;

  // Display user query
  appendMessage("user", query);

  // Display loading animation
  appendMessage("system", "Searching...");

  try {
    const response = await fetch("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await response.json();

    if (response.ok) {
      // Display AI summary
      appendMessage("system", data.summary || "No results found.");

      // Display top links
      if (data.links && data.links.length > 0) {
        appendMessage("system", "Top referenced websites:");
        data.links.forEach((link) => {
          appendMessage(
            "system",
            `<a href="${link.url}" target="_blank">${link.title}</a> (Grade: ${link.grade}/10)`
          );
        });
      }
    } else {
      appendMessage("system", `Error: ${data.error}`);
    }
  } catch (error) {
    appendMessage("system", `Error: ${error.message}`);
  }

  userInput.value = ""; // Clear the input field after submission
});

// Handle form submission for code optimization
const optimizeForm = document.getElementById("optimizeForm");
const codeInput = document.getElementById("codeInput");

optimizeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const codeSnippet = codeInput.value.trim();
  if (!codeSnippet) return;

  // Display user input
  appendMessage("user", "Optimize this code snippet:");
  appendMessage("user", `<pre><code>${codeSnippet}</code></pre>`);

  // Display loading animation
  appendMessage("system", "Analyzing and optimizing code...");

  try {
    const response = await fetch("/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code_snippet: codeSnippet }),
    });

    const data = await response.json();

    if (response.ok) {
      // Display original code
      appendMessage("system", "Original Code:");
      appendMessage("system", `<pre><code>${data.original_code}</code></pre>`);

      // Display optimized code
      appendMessage("system", "Optimized Code:");
      appendMessage("system", `<pre><code>${data.optimized_code}</code></pre>`);

      // Display grading (optional)
      appendMessage(
        "system",
        `Grading: ${data.grade || "N/A"} (0: low, 1: moderate, 2: high)`
      );
    } else {
      appendMessage("system", `Error: ${data.error}`);
    }
  } catch (error) {
    appendMessage("system", `Error: ${error.message}`);
  }

  codeInput.value = ""; // Clear the input field after submission
});

// Append message with clickable links and formatted content
function appendMessage(sender, message) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);

  // Format content by removing markdown symbols like ###, **, *, etc.
  const formattedContent = message
    .replace(/###\s?(.*?):/g, "<h4>$1:</h4>") // Convert headings (###) to h4
    .replace(/####\s?(.*)/g, "<h5>$1</h5>") // Convert smaller headings (####) to h5
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") // Convert bold (**text**) to <strong>
    .replace(/\*(.*?)\*/g, "<em>$1</em>") // Convert italic (*text*) to <em>
    .replace(/```\s?python/g, '<pre><code class="python">') // Start of code block (Python)
    .replace(/```/g, "</code></pre>") // End of code block
    .replace(/\n/g, "<br>"); // Convert newlines to <br> for line breaks

  // The content will no longer have markdown syntax like ### or **
  const content = `
    <div class="message-content">
        <div class="message-bubble">
            <div class="message-text">
                ${formattedContent}
            </div>
        </div>
    </div>`;

  messageDiv.innerHTML = content;

  const chatMessages = document.getElementById("chatMessages");
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom
}
