#!/usr/bin/env node
/**
 * ASCII Art → PNG Renderer
 *
 * Renders ASCII art (diagrams, flowcharts, architecture charts, timelines)
 * into clean, light-themed code-editor style PNG images with:
 *   - macOS-style title bar (red/yellow/green dots)
 *   - Line numbers
 *   - Monospace font (Consolas / Monaco)
 *   - Retina resolution (2x)
 *
 * Usage:
 *   node render.js <input.txt> <output.png>
 *   node render.js --text "Hello World" output.png
 *   node render.js input.txt output.png --title "My Diagram"
 *   node render.js input.txt output.png --no-line-numbers
 *   node render.js input.txt output.png --dark
 *
 * Options:
 *   --title <text>      Show a title in the title bar
 *   --no-line-numbers   Hide line numbers
 *   --dark              Use dark theme instead of light
 *   --scale <n>         Device scale factor (default: 2 for Retina)
 *   --font-size <n>     Font size in px (default: 14)
 *
 * Requirements:
 *   npm install puppeteer
 *
 * Supports Unicode box-drawing characters, arrows, and emoji.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const os = require('os');

// ─── Themes ──────────────────────────────────────────────

const THEMES = {
  light: {
    bg: '#fafbfc',
    border: '#e1e4e8',
    titlebar: '#f1f3f5',
    text: '#24292e',
    lineNum: '#959da5',
    dots: ['#ff5f56', '#ffbd2e', '#27c93f'],
    titleText: '#6a737d',
  },
  dark: {
    bg: '#1e1e2e',
    border: '#313244',
    titlebar: '#181825',
    text: '#cdd6f4',
    lineNum: '#585b70',
    dots: ['#f38ba8', '#f9e2af', '#a6e3a1'],
    titleText: '#a6adc8',
  },
};

// ─── HTML generation ─────────────────────────────────────

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function generateHtml(code, options = {}) {
  const {
    theme = 'light',
    title = '',
    showLineNumbers = true,
    fontSize = 14,
  } = options;

  const t = THEMES[theme] || THEMES.light;
  const lines = code.split('\n');

  // Remove trailing empty lines
  while (lines.length > 0 && lines[lines.length - 1].trim() === '') {
    lines.pop();
  }

  const lineCount = lines.length;
  const maxLineNumWidth = String(lineCount).length;

  const linesHtml = lines
    .map((line, i) => {
      const num = String(i + 1).padStart(maxLineNumWidth, ' ');
      const numSpan = showLineNumbers
        ? `<span class="line-num">${num}</span>`
        : '';
      return `<div class="line">${numSpan}<span class="line-content">${escapeHtml(line)}</span></div>`;
    })
    .join('');

  const titleHtml = title
    ? `<span class="title-text">${escapeHtml(title)}</span>`
    : '';

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: transparent;
    display: inline-block;
  }
  .container {
    background: ${t.bg};
    border: 1px solid ${t.border};
    border-radius: 8px;
    overflow: hidden;
    display: inline-block;
  }
  .titlebar {
    background: ${t.titlebar};
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    border-bottom: 1px solid ${t.border};
  }
  .dot { width: 10px; height: 10px; border-radius: 50%; }
  .dot-0 { background: ${t.dots[0]}; }
  .dot-1 { background: ${t.dots[1]}; }
  .dot-2 { background: ${t.dots[2]}; }
  .title-text {
    margin-left: 10px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 12px;
    color: ${t.titleText};
  }
  .code-body {
    padding: 16px 20px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: ${fontSize}px;
    line-height: 1.6;
    color: ${t.text};
    white-space: pre;
  }
  .line {
    display: block;
    min-height: 1.6em;
  }
  .line-num {
    color: ${t.lineNum};
    margin-right: 20px;
    user-select: none;
    display: inline-block;
    text-align: right;
    min-width: ${maxLineNumWidth}ch;
  }
  .line-content {
    color: ${t.text};
  }
</style>
</head>
<body>
<div class="container">
  <div class="titlebar">
    <div class="dot dot-0"></div>
    <div class="dot dot-1"></div>
    <div class="dot dot-2"></div>
    ${titleHtml}
  </div>
  <div class="code-body">${linesHtml}</div>
</div>
</body>
</html>`;
}

// ─── Renderer ────────────────────────────────────────────

async function render(asciiText, outputPath, options = {}) {
  const { scale = 2 } = options;
  const html = generateHtml(asciiText, options);

  const tmpHtml = path.join(os.tmpdir(), `ascii_render_${Date.now()}.html`);
  fs.writeFileSync(tmpHtml, html, 'utf8');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: scale });
    await page.goto(`file://${tmpHtml}`, { waitUntil: 'networkidle0' });

    const container = await page.$('.container');
    const box = await container.boundingBox();

    const outDir = path.dirname(outputPath);
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    await page.screenshot({
      path: outputPath,
      clip: { x: box.x, y: box.y, width: box.width, height: box.height },
      omitBackground: true,
    });

    const result = {
      success: true,
      output: outputPath,
      width: Math.round(box.width * scale),
      height: Math.round(box.height * scale),
    };

    console.log(JSON.stringify(result));
    return result;
  } finally {
    await browser.close();
    try { fs.unlinkSync(tmpHtml); } catch (_) {}
  }
}

// ─── CLI ─────────────────────────────────────────────────

function parseArgs(argv) {
  const args = argv.slice(2);
  const opts = {
    input: null,
    output: null,
    title: '',
    showLineNumbers: true,
    theme: 'light',
    scale: 2,
    fontSize: 14,
    inlineText: null,
  };

  let i = 0;
  while (i < args.length) {
    switch (args[i]) {
      case '--text':
        opts.inlineText = args[++i];
        break;
      case '--title':
        opts.title = args[++i];
        break;
      case '--no-line-numbers':
        opts.showLineNumbers = false;
        break;
      case '--dark':
        opts.theme = 'dark';
        break;
      case '--scale':
        opts.scale = parseInt(args[++i], 10) || 2;
        break;
      case '--font-size':
        opts.fontSize = parseInt(args[++i], 10) || 14;
        break;
      case '--help':
      case '-h':
        console.log(`
ASCII Art → PNG Renderer

Usage:
  node render.js <input.txt> <output.png> [options]
  node render.js --text "ascii art" <output.png> [options]

Options:
  --title <text>       Title shown in the title bar
  --no-line-numbers    Hide line numbers
  --dark               Use dark theme
  --scale <n>          Scale factor (default: 2)
  --font-size <n>      Font size in px (default: 14)
  -h, --help           Show this help
`);
        process.exit(0);
        break;
      default:
        if (!opts.input && !opts.inlineText) opts.input = args[i];
        else if (!opts.output) opts.output = args[i];
        break;
    }
    i++;
  }

  return opts;
}

(async () => {
  const opts = parseArgs(process.argv);

  if (!opts.output) {
    console.error('Error: Missing output path. Run with --help for usage.');
    process.exit(1);
  }

  let asciiText;
  if (opts.inlineText) {
    asciiText = opts.inlineText;
  } else if (opts.input) {
    if (!fs.existsSync(opts.input)) {
      console.error(`Error: Input file not found: ${opts.input}`);
      process.exit(1);
    }
    asciiText = fs.readFileSync(opts.input, 'utf8');
  } else {
    console.error('Error: No input specified. Run with --help for usage.');
    process.exit(1);
  }

  const outputPath = path.resolve(opts.output);
  await render(asciiText, outputPath, {
    title: opts.title,
    showLineNumbers: opts.showLineNumbers,
    theme: opts.theme,
    scale: opts.scale,
    fontSize: opts.fontSize,
  });
})();
