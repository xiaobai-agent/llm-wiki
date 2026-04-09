# 🛠️ Tools

Standalone utilities that complement your LLM Wiki knowledge base.

## Available Tools

### [ASCII Renderer](./ascii-renderer/)

Render ASCII art diagrams into publication-ready PNG images with a code-editor aesthetic. Perfect for architecture diagrams, flowcharts, and timelines in your documentation.

```bash
npm install puppeteer
node tools/ascii-renderer/render.js diagram.txt output.png --title "Architecture"
```

**Features:** Light & dark themes, line numbers, Retina resolution, Unicode + emoji support.

### [Schema Validator](./schema-validator/)

Validate your wiki structure against the WIKI-SCHEMA.md specification. Catches missing directories, broken links, frontmatter issues, and orphan pages.

```bash
# No dependencies needed!
node tools/schema-validator/validate.js ./wiki
```

**Features:** Structure checks, frontmatter validation, cross-reference verification, health metrics, JSON output for CI, auto-fix mode.

## Contributing

Each tool is self-contained in its own directory with its own README. Feel free to extend or customize them for your workflow.
