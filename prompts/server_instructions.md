# Basic MCP Server

This server provides tools for working with Wikipedia topics, summaries, and related links.

## Available Tools

### fetch_wikipedia_summary
Retrieves a concise summary and related links for a given topic from Wikipedia.

**Parameters:**
- `topic` (string): The topic to search on Wikipedia

**Returns:** 
- A formatted summary (first ~5 sentences)  
- A list of up to 10 related links from the page  
- Handles disambiguation and missing pages gracefully

**Usage:** Call this tool whenever you need to extract basic details or related links about a topic from Wikipedia.

---

### fetch_instructions
Retrieves specialized instruction templates for working with Wikipedia summaries.

**Parameters:**
- `prompt_name` (string): Must be one of:
  - `fetch_wikipedia_summary` – Guidelines for fetching and formatting Wikipedia content

**Returns:** Detailed instructions and formatting requirements for the requested content type

**Usage:** Fetch these instructions before performing content transformation tasks to ensure proper formatting and structure.
