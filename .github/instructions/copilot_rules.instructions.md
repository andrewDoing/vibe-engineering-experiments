---
description: "Guidelines for creating and maintaining copilot instructions to ensure consistency and effectiveness."
applyTo: ".github/instructions/*.instructions.md"
---

- **Required Rule Structure:**
  ```markdown
  ---
  mode: "agent" or "ask" or "edit"
  description: Clear, one-line description of what the rule enforces
  applyTo: ".github/instructions/*.instructions.md"
  ---

  - **Main Points in Bold**
    - Sub-points with details
    - Examples and explanations
  ```

- **File References:**
  - Use `[filename](path/to/filename)` to reference files
  - Example: [prisma.instructions.md](prisma.instructions.md) for rule references
  - Example: [schema.prisma](prisma/schema.prisma) for code references

- **Code Examples:**
  - Use language-specific code blocks
  ```typescript
  // ✅ DO: Show good examples
  const goodExample = true;
  
  // ❌ DON'T: Show anti-patterns
  const badExample = false;
  ```

- **Rule Content Guidelines:**
  - Start with high-level overview
  - Include specific, actionable requirements
  - Show examples of correct implementation
  - Reference existing code when possible
  - Keep rules DRY by referencing other rules

- **Rule Maintenance:**
  - Update rules when new patterns emerge
  - Add examples from actual codebase
  - Remove outdated patterns
  - Cross-reference related rules

- **Best Practices:**
  - Use bullet points for clarity
  - Keep descriptions concise
  - Include both DO and DON'T examples
  - Reference actual code over theoretical examples
  - Use consistent formatting across rules 