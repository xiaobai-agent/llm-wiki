#!/usr/bin/env node
/**
 * LLM Wiki Schema Validator
 *
 * Validates a wiki directory against the WIKI-SCHEMA.md specification.
 * Checks structure, frontmatter, cross-references, and health metrics.
 *
 * Usage:
 *   node validate.js <wiki_directory>
 *   node validate.js ./wiki
 *   node validate.js ./wiki --json
 *   node validate.js ./wiki --fix
 *
 * Options:
 *   --json    Output results as JSON (for automation)
 *   --fix     Auto-fix simple issues (create missing dirs, update index)
 *   --strict  Treat warnings as errors (exit code 1 on warnings)
 *   -h        Show help
 *
 * Exit codes:
 *   0 = all checks passed
 *   1 = errors found
 *   2 = invalid arguments
 */

const fs = require('fs');
const path = require('path');

// ─── Expected Structure ──────────────────────────────────

const REQUIRED_DIRS = [
  'raw',
  'raw/articles',
  'raw/notes',
  'raw/videos',
  'raw/other',
  'pages',
  'pages/concepts',
  'pages/entities',
  'pages/sources',
  'pages/comparisons',
  'pages/insights',
  'meta',
];

const REQUIRED_FILES = [
  'index.md',
];

const META_FILES = [
  'meta/ingest-strategies.md',
  'meta/research-patterns.md',
  'meta/source-quality.md',
  'meta/failure-log.md',
];

const VALID_PAGE_TYPES = ['concept', 'entity', 'source', 'comparison', 'insight'];
const VALID_CONFIDENCE = ['high', 'medium', 'low'];

const REQUIRED_FRONTMATTER = ['title', 'type', 'created'];
const RECOMMENDED_FRONTMATTER = ['tags', 'sources', 'related', 'updated', 'confidence'];

// ─── Result Collectors ───────────────────────────────────

class ValidationReport {
  constructor(wikiDir) {
    this.wikiDir = wikiDir;
    this.errors = [];
    this.warnings = [];
    this.info = [];
    this.stats = {
      totalPages: 0,
      totalRawFiles: 0,
      pagesByType: {},
      pagesByConfidence: {},
      orphanPages: [],
      missingLinks: [],
      duplicateTitles: [],
    };
  }

  error(msg, file = null) {
    this.errors.push({ message: msg, file });
  }
  warn(msg, file = null) {
    this.warnings.push({ message: msg, file });
  }
  note(msg) {
    this.info.push(msg);
  }

  get passed() {
    return this.errors.length === 0;
  }

  toJSON() {
    return {
      passed: this.passed,
      wikiDir: this.wikiDir,
      errors: this.errors,
      warnings: this.warnings,
      info: this.info,
      stats: this.stats,
    };
  }

  print() {
    const { errors, warnings, info, stats } = this;

    console.log('\n╔══════════════════════════════════════════╗');
    console.log('║     📋 LLM Wiki Validation Report       ║');
    console.log('╚══════════════════════════════════════════╝\n');

    console.log(`  Wiki directory: ${this.wikiDir}\n`);

    // Stats
    console.log('  📊 Statistics');
    console.log(`     Pages: ${stats.totalPages}`);
    console.log(`     Raw sources: ${stats.totalRawFiles}`);
    if (Object.keys(stats.pagesByType).length > 0) {
      console.log('     By type:');
      for (const [type, count] of Object.entries(stats.pagesByType)) {
        console.log(`       ${type}: ${count}`);
      }
    }
    if (Object.keys(stats.pagesByConfidence).length > 0) {
      console.log('     By confidence:');
      for (const [level, count] of Object.entries(stats.pagesByConfidence)) {
        console.log(`       ${level}: ${count}`);
      }
    }
    console.log('');

    // Errors
    if (errors.length > 0) {
      console.log(`  ❌ Errors (${errors.length})`);
      errors.forEach((e) => {
        const loc = e.file ? ` [${e.file}]` : '';
        console.log(`     • ${e.message}${loc}`);
      });
      console.log('');
    }

    // Warnings
    if (warnings.length > 0) {
      console.log(`  ⚠️  Warnings (${warnings.length})`);
      warnings.forEach((w) => {
        const loc = w.file ? ` [${w.file}]` : '';
        console.log(`     • ${w.message}${loc}`);
      });
      console.log('');
    }

    // Info
    if (info.length > 0) {
      console.log(`  ℹ️  Notes`);
      info.forEach((n) => console.log(`     • ${n}`));
      console.log('');
    }

    // Orphans
    if (stats.orphanPages.length > 0) {
      console.log(`  🔗 Orphan pages (not linked from any other page)`);
      stats.orphanPages.forEach((p) => console.log(`     • ${p}`));
      console.log('');
    }

    // Missing links
    if (stats.missingLinks.length > 0) {
      console.log(`  🔍 Broken links`);
      stats.missingLinks.forEach(({ from, to }) => {
        console.log(`     • ${from} → ${to}`);
      });
      console.log('');
    }

    // Verdict
    if (this.passed) {
      console.log('  ✅ All checks passed!\n');
    } else {
      console.log(`  ❌ ${errors.length} error(s) found. Please fix them.\n`);
    }
  }
}

// ─── Frontmatter Parser ─────────────────────────────────

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;

  const yaml = match[1];
  const result = {};

  // Simple YAML parser (handles the fields we care about)
  const lines = yaml.split('\n');
  let currentKey = null;
  let currentList = null;

  for (const line of lines) {
    // List item
    const listMatch = line.match(/^\s+-\s+(.+)/);
    if (listMatch && currentKey && currentList) {
      currentList.push(listMatch[1].trim());
      continue;
    }

    // Key-value
    const kvMatch = line.match(/^(\w[\w-]*):\s*(.*)/);
    if (kvMatch) {
      // Save previous list
      if (currentKey && currentList) {
        result[currentKey] = currentList;
      }

      currentKey = kvMatch[1];
      const val = kvMatch[2].trim();

      // Inline array: [a, b, c]
      const arrMatch = val.match(/^\[(.+)\]$/);
      if (arrMatch) {
        result[currentKey] = arrMatch[1].split(',').map((s) => s.trim().replace(/^["']|["']$/g, ''));
        currentList = null;
        continue;
      }

      // Empty value → might be start of a list
      if (val === '' || val === '[]') {
        currentList = [];
        continue;
      }

      result[currentKey] = val.replace(/^["']|["']$/g, '');
      currentList = null;
    }
  }

  // Save last list
  if (currentKey && currentList) {
    result[currentKey] = currentList;
  }

  return result;
}

// ─── File Discovery ──────────────────────────────────────

function findMarkdownFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) {
      results.push(...findMarkdownFiles(fullPath));
    } else if (item.name.endsWith('.md') && item.name !== '.gitkeep') {
      results.push(fullPath);
    }
  }
  return results;
}

// ─── Validators ──────────────────────────────────────────

function checkStructure(wikiDir, report, autoFix) {
  // Check required directories
  for (const dir of REQUIRED_DIRS) {
    const fullPath = path.join(wikiDir, dir);
    if (!fs.existsSync(fullPath)) {
      if (autoFix) {
        fs.mkdirSync(fullPath, { recursive: true });
        report.note(`Created missing directory: ${dir}`);
      } else {
        report.error(`Missing required directory: ${dir}`);
      }
    }
  }

  // Check required files
  for (const file of REQUIRED_FILES) {
    const fullPath = path.join(wikiDir, file);
    if (!fs.existsSync(fullPath)) {
      if (autoFix) {
        fs.writeFileSync(fullPath, `# Wiki Index\n\n_Auto-generated. Update after each change._\n`, 'utf8');
        report.note(`Created missing file: ${file}`);
      } else {
        report.error(`Missing required file: ${file}`);
      }
    }
  }

  // Check meta files (recommended, not required)
  for (const file of META_FILES) {
    const fullPath = path.join(wikiDir, file);
    if (!fs.existsSync(fullPath)) {
      report.warn(`Missing recommended meta file: ${file}`);
    }
  }
}

function checkPages(wikiDir, report) {
  const pagesDir = path.join(wikiDir, 'pages');
  const pageFiles = findMarkdownFiles(pagesDir);
  const allTitles = new Map(); // title → file path
  const allPagePaths = new Set(); // relative paths for link checking
  const incomingLinks = new Map(); // page → set of pages that link to it
  const allLinks = []; // { from, to } for broken link detection

  report.stats.totalPages = pageFiles.length;

  for (const filePath of pageFiles) {
    const relPath = path.relative(wikiDir, filePath).replace(/\\/g, '/');
    allPagePaths.add(relPath);
    incomingLinks.set(relPath, new Set());
  }

  for (const filePath of pageFiles) {
    const relPath = path.relative(wikiDir, filePath).replace(/\\/g, '/');
    const content = fs.readFileSync(filePath, 'utf8');

    // Parse frontmatter
    const fm = parseFrontmatter(content);
    if (!fm) {
      report.error('Missing YAML frontmatter', relPath);
      continue;
    }

    // Check required fields
    for (const field of REQUIRED_FRONTMATTER) {
      if (!fm[field]) {
        report.error(`Missing required frontmatter field: ${field}`, relPath);
      }
    }

    // Check recommended fields
    for (const field of RECOMMENDED_FRONTMATTER) {
      if (!fm[field]) {
        report.warn(`Missing recommended frontmatter field: ${field}`, relPath);
      }
    }

    // Validate type
    if (fm.type && !VALID_PAGE_TYPES.includes(fm.type)) {
      report.error(
        `Invalid page type: "${fm.type}" (valid: ${VALID_PAGE_TYPES.join(', ')})`,
        relPath
      );
    }

    // Validate confidence
    if (fm.confidence && !VALID_CONFIDENCE.includes(fm.confidence)) {
      report.warn(
        `Invalid confidence level: "${fm.confidence}" (valid: ${VALID_CONFIDENCE.join(', ')})`,
        relPath
      );
    }

    // Check date format
    if (fm.created && !/^\d{4}-\d{2}-\d{2}/.test(fm.created)) {
      report.warn(`Invalid date format for 'created': ${fm.created}`, relPath);
    }
    if (fm.updated && !/^\d{4}-\d{2}-\d{2}/.test(fm.updated)) {
      report.warn(`Invalid date format for 'updated': ${fm.updated}`, relPath);
    }

    // Count by type
    if (fm.type) {
      report.stats.pagesByType[fm.type] = (report.stats.pagesByType[fm.type] || 0) + 1;
    }

    // Count by confidence
    if (fm.confidence) {
      report.stats.pagesByConfidence[fm.confidence] =
        (report.stats.pagesByConfidence[fm.confidence] || 0) + 1;
    }

    // Duplicate title check
    if (fm.title) {
      const lower = fm.title.toLowerCase();
      if (allTitles.has(lower)) {
        report.stats.duplicateTitles.push({ title: fm.title, files: [allTitles.get(lower), relPath] });
        report.warn(`Duplicate title: "${fm.title}"`, relPath);
      } else {
        allTitles.set(lower, relPath);
      }
    }

    // Collect links (sources and related)
    const linkedPaths = [];
    if (Array.isArray(fm.sources)) linkedPaths.push(...fm.sources);
    if (Array.isArray(fm.related)) linkedPaths.push(...fm.related);

    for (const link of linkedPaths) {
      // Normalize link path
      const normalized = link.replace(/\\/g, '/').replace(/^\.\//, '');
      allLinks.push({ from: relPath, to: normalized });

      // Track incoming links
      if (incomingLinks.has(normalized)) {
        incomingLinks.get(normalized).add(relPath);
      }
    }
  }

  // Check for broken links
  for (const { from, to } of allLinks) {
    const fullTarget = path.join(wikiDir, to);
    if (!fs.existsSync(fullTarget)) {
      report.stats.missingLinks.push({ from, to });
      report.warn(`Broken link: references "${to}" which does not exist`, from);
    }
  }

  // Find orphan pages (no incoming links from other pages, excluding index)
  for (const [pagePath, links] of incomingLinks) {
    if (links.size === 0 && !pagePath.endsWith('index.md')) {
      report.stats.orphanPages.push(pagePath);
    }
  }
  if (report.stats.orphanPages.length > 0) {
    report.warn(`${report.stats.orphanPages.length} orphan page(s) found (not linked from any other page)`);
  }
}

function checkRawFiles(wikiDir, report) {
  const rawDir = path.join(wikiDir, 'raw');
  const rawFiles = findMarkdownFiles(rawDir);
  report.stats.totalRawFiles = rawFiles.length;

  // Check naming convention: YYYY-MM-DD-title.md
  const datePattern = /^\d{4}-\d{2}-\d{2}-.+\.md$/;
  for (const filePath of rawFiles) {
    const fileName = path.basename(filePath);
    if (!datePattern.test(fileName)) {
      report.warn(
        `Raw file doesn't follow naming convention (YYYY-MM-DD-title.md): ${fileName}`,
        path.relative(wikiDir, filePath).replace(/\\/g, '/')
      );
    }
  }
}

function checkIndex(wikiDir, report) {
  const indexPath = path.join(wikiDir, 'index.md');
  if (!fs.existsSync(indexPath)) return;

  const indexContent = fs.readFileSync(indexPath, 'utf8');
  const pagesDir = path.join(wikiDir, 'pages');
  const pageFiles = findMarkdownFiles(pagesDir);

  // Check if all pages are mentioned in index
  const missingFromIndex = [];
  for (const filePath of pageFiles) {
    const relPath = path.relative(wikiDir, filePath).replace(/\\/g, '/');
    const fileName = path.basename(filePath, '.md');
    // Check if filename or path appears in index
    if (!indexContent.includes(fileName) && !indexContent.includes(relPath)) {
      missingFromIndex.push(relPath);
    }
  }

  if (missingFromIndex.length > 0) {
    report.warn(`${missingFromIndex.length} page(s) not listed in index.md`);
    for (const p of missingFromIndex.slice(0, 10)) {
      report.note(`Not in index: ${p}`);
    }
    if (missingFromIndex.length > 10) {
      report.note(`...and ${missingFromIndex.length - 10} more`);
    }
  }
}

// ─── Main ────────────────────────────────────────────────

function validate(wikiDir, options = {}) {
  const { autoFix = false } = options;
  const report = new ValidationReport(path.resolve(wikiDir));

  if (!fs.existsSync(wikiDir)) {
    report.error(`Wiki directory not found: ${wikiDir}`);
    return report;
  }

  checkStructure(wikiDir, report, autoFix);
  checkPages(wikiDir, report);
  checkRawFiles(wikiDir, report);
  checkIndex(wikiDir, report);

  return report;
}

// ─── CLI ─────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
    console.log(`
📋 LLM Wiki Schema Validator

Usage:
  node validate.js <wiki_directory> [options]

Options:
  --json      Output results as JSON
  --fix       Auto-fix simple issues (create missing dirs/files)
  --strict    Treat warnings as errors
  -h, --help  Show this help

Examples:
  node validate.js ./wiki
  node validate.js ./wiki --json
  node validate.js ./wiki --fix
`);
    process.exit(args.length === 0 ? 2 : 0);
  }

  const wikiDir = args.find((a) => !a.startsWith('--'));
  const jsonOutput = args.includes('--json');
  const autoFix = args.includes('--fix');
  const strict = args.includes('--strict');

  if (!wikiDir) {
    console.error('Error: No wiki directory specified.');
    process.exit(2);
  }

  const report = validate(wikiDir, { autoFix });

  if (jsonOutput) {
    console.log(JSON.stringify(report.toJSON(), null, 2));
  } else {
    report.print();
  }

  const hasIssues = report.errors.length > 0 || (strict && report.warnings.length > 0);
  process.exit(hasIssues ? 1 : 0);
}

main();
