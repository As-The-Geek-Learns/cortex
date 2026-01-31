#!/usr/bin/env node

/**
 * Verification Script (Python project)
 * =====================================
 * Generates verification state including:
 * - SHA256 hashes of source and test files (src/, tests/, .py, .json, etc.)
 * - Test results (pytest via npm test)
 * - Lint status (ruff via npm run lint)
 * - Security audit (pip-audit via npm run audit)
 * - AI code review (Gemini)
 *
 * Usage: node scripts/verify.js [options]
 *
 * Options:
 *   --skip-tests       Skip running tests
 *   --skip-lint        Skip running linter
 *   --skip-ai-review   Skip AI code review
 *   --security-focus   Focus AI review on security only
 *
 * Environment:
 *   GEMINI_API_KEY     Required for AI review (optional if --skip-ai-review)
 */

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// Configuration: Python project — hash src/ and tests/, include .py and .json
const DEFAULT_EXTENSIONS = [".py", ".json", ".js", ".jsx", ".ts", ".tsx", ".css"];
const OUTPUT_PATH = ".workflow/state/verify-state.json";
const DIRS_TO_SCAN = ["src", "tests"]; // Python project layout
const DIRS_TO_SKIP = ["node_modules", ".venv", "venv", "__pycache__", ".ruff_cache", ".pytest_cache"];

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  skipTests: args.includes("--skip-tests"),
  skipLint: args.includes("--skip-lint"),
  skipAiReview: args.includes("--skip-ai-review"),
  securityFocus: args.includes("--security-focus"),
  outputPath: OUTPUT_PATH,
};

function hashFile(filePath) {
  try {
    const content = fs.readFileSync(filePath);
    return crypto.createHash("sha256").update(content).digest("hex");
  } catch (error) {
    console.error("Error hashing " + filePath + ":", error.message);
    return null;
  }
}

function findFiles(baseDir) {
  const files = [];

  function walkDir(dir) {
    if (!fs.existsSync(dir)) return;

    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.name.startsWith(".") && entry.name !== ".cursor") continue;
      if (DIRS_TO_SKIP.includes(entry.name)) continue;

      if (entry.isDirectory()) {
        walkDir(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (DEFAULT_EXTENSIONS.includes(ext)) {
          files.push(fullPath);
        }
      }
    }
  }

  for (const dirName of DIRS_TO_SCAN) {
    const dirPath = path.join(baseDir, dirName);
    if (fs.existsSync(dirPath)) {
      walkDir(dirPath);
    }
  }

  if (files.length === 0) {
    console.log("No src/ or tests/ directories found. Scanning current directory...");
    walkDir(baseDir);
  }

  return files.sort();
}

function runCommand(command, description) {
  console.log("\n" + description + "...");
  try {
    const output = execSync(command, {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    return { success: true, output: output.trim() };
  } catch (error) {
    return {
      success: false,
      output: error.stdout ? error.stdout.trim() : "",
      error: error.stderr ? error.stderr.trim() : error.message,
    };
  }
}

function runTests() {
  if (options.skipTests) {
    console.log("Skipping tests (--skip-tests)");
    return { skipped: true };
  }

  try {
    const pkg = JSON.parse(fs.readFileSync("package.json", "utf-8"));
    if (!pkg.scripts || !pkg.scripts.test) {
      console.log("No test script found in package.json");
      return { skipped: true, reason: "no test script" };
    }
  } catch (e) {
    console.log("No package.json found");
    return { skipped: true, reason: "no package.json" };
  }

  const result = runCommand("npm test 2>&1", "Running tests");
  return {
    success: result.success,
    output: result.output,
    error: result.error,
  };
}

function runLint() {
  if (options.skipLint) {
    console.log("Skipping lint (--skip-lint)");
    return { skipped: true };
  }

  try {
    const pkg = JSON.parse(fs.readFileSync("package.json", "utf-8"));
    if (!pkg.scripts || !pkg.scripts.lint) {
      console.log("No lint script found in package.json");
      return { skipped: true, reason: "no lint script" };
    }
  } catch (e) {
    return { skipped: true, reason: "no package.json" };
  }

  const result = runCommand("npm run lint 2>&1", "Running linter");
  return {
    success: result.success,
    output: result.output,
    error: result.error,
  };
}

function runAudit() {
  // This project: npm run audit runs pip-audit
  const result = runCommand("npm run audit 2>&1", "Running security audit (pip-audit)");
  return {
    success: result.success,
    output: (result.output || "").substring(0, 500),
  };
}

function runAiReview() {
  if (options.skipAiReview) {
    console.log("Skipping AI review (--skip-ai-review)");
    return { skipped: true };
  }

  if (!process.env.GEMINI_API_KEY) {
    console.log("No GEMINI_API_KEY set, skipping AI review");
    console.log("Set with: export GEMINI_API_KEY=\"your-key\"");
    return { skipped: true, reason: "no API key" };
  }

  const aiReviewPath = path.join(__dirname, "ai-review.js");
  if (!fs.existsSync(aiReviewPath)) {
    console.log("AI review script not found");
    return { skipped: true, reason: "script not found" };
  }

  console.log("\nRunning AI Code Review (Gemini)...");

  try {
    const aiArgs = options.securityFocus ? "--security-focus" : "";
    execSync("node " + aiReviewPath + " " + aiArgs, {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
      env: process.env,
      timeout: 120000,
    });
  } catch (error) {
    // AI review may exit 1 when issues found; we still read the result file
  }

  const aiResultPath = ".workflow/state/ai-review.json";
  if (fs.existsSync(aiResultPath)) {
    try {
      const aiResults = JSON.parse(fs.readFileSync(aiResultPath, "utf-8"));
      return {
        success: aiResults.summary && aiResults.summary.passesReview,
        securityRisk: aiResults.summary && aiResults.summary.securityRisk,
        codeQuality: aiResults.summary && aiResults.summary.codeQuality,
        securityIssues: (aiResults.securityReview && aiResults.securityReview.issues && aiResults.securityReview.issues.length) || 0,
        qualityIssues: (aiResults.qualityReview && aiResults.qualityReview.issues && aiResults.qualityReview.issues.length) || 0,
        needsAttention: aiResults.summary && !aiResults.summary.passesReview,
      };
    } catch (e) {
      // ignore parse errors
    }
  }

  return { success: true };
}

async function main() {
  console.log("=".repeat(60));
  console.log("VERIFICATION SCRIPT (Python project)");
  console.log("=".repeat(60));
  console.log("Timestamp: " + new Date().toISOString());

  console.log("\nFinding source and test files...");
  const files = findFiles(".");
  console.log("Found " + files.length + " files to hash");

  const fileHashes = {};
  for (const file of files) {
    const hash = hashFile(file);
    if (hash) {
      fileHashes[file] = hash;
    }
  }

  const testResults = runTests();
  const lintResults = runLint();
  const auditResults = runAudit();
  const aiReviewResults = runAiReview();

  const verifyState = {
    version: "1.1.0",
    timestamp: new Date().toISOString(),
    files: {
      count: Object.keys(fileHashes).length,
      hashes: fileHashes,
    },
    tests: testResults,
    lint: lintResults,
    audit: auditResults,
    aiReview: aiReviewResults,
    summary: {
      filesHashed: Object.keys(fileHashes).length,
      testsPass: testResults.success || testResults.skipped,
      lintPass: lintResults.success || lintResults.skipped,
      auditPass: auditResults.success,
      aiReviewPass: aiReviewResults.success || aiReviewResults.skipped,
      overallPass:
        (testResults.success || testResults.skipped) &&
        (lintResults.success || lintResults.skipped) &&
        auditResults.success &&
        (aiReviewResults.success || aiReviewResults.skipped),
    },
  };

  const outputDir = path.dirname(options.outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(options.outputPath, JSON.stringify(verifyState, null, 2));

  console.log("\n" + "=".repeat(60));
  console.log("VERIFICATION SUMMARY");
  console.log("=".repeat(60));
  console.log("Files hashed:    " + verifyState.summary.filesHashed);
  console.log("Tests:           " + (verifyState.summary.testsPass ? "PASS" : "FAIL"));
  console.log("Lint:            " + (verifyState.summary.lintPass ? "PASS" : "FAIL"));
  console.log("Security Audit:  " + (verifyState.summary.auditPass ? "PASS" : "FAIL"));
  console.log("AI Review:       " + (verifyState.summary.aiReviewPass ? "PASS" : "NEEDS ATTENTION"));

  if (aiReviewResults.securityRisk) {
    console.log("  Security Risk: " + aiReviewResults.securityRisk);
  }
  if (aiReviewResults.codeQuality) {
    console.log("  Code Quality:  " + aiReviewResults.codeQuality);
  }

  console.log("-".repeat(60));
  console.log("OVERALL:         " + (verifyState.summary.overallPass ? "PASS" : "FAIL"));
  console.log("=".repeat(60));
  console.log("\nVerification state written to: " + options.outputPath);

  if (aiReviewResults.needsAttention) {
    console.log("\nNote: AI review found issues that need attention.");
    console.log("Review details in: .workflow/state/ai-review.json");
  }

  process.exit(verifyState.summary.overallPass ? 0 : 1);
}

main().catch(function (error) {
  console.error("Verification failed:", error);
  process.exit(1);
});
