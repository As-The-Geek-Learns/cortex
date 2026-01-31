#!/usr/bin/env node

/**
 * AI Code Review Script (Gemini)
 * ==============================
 * Sends code to Google Gemini for security and quality review.
 * Python project: reviews src/ and tests/ (.py and common extensions).
 *
 * Usage: node scripts/ai-review.js [options]
 *
 * Options:
 *   --files <paths>    Comma-separated file paths to review
 *   --diff             Review git diff instead of full files
 *   --security-focus   Focus review on security concerns
 *   --output <path>    Output path for review results
 *
 * Environment:
 *   GEMINI_API_KEY     Required. Your Google Gemini API key.
 */

const fs = require("fs");
const path = require("path");
const https = require("https");
const { execSync } = require("child_process");

// Configuration
const GEMINI_API_URL = "generativelanguage.googleapis.com";
const GEMINI_MODEL = "gemini-2.5-flash";
const OUTPUT_PATH = ".workflow/state/ai-review.json";
const MAX_FILE_SIZE = 50000;

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  useDiff: args.includes("--diff"),
  securityFocus: args.includes("--security-focus"),
  outputPath: OUTPUT_PATH,
  files: [],
};

const filesIndex = args.indexOf("--files");
if (filesIndex !== -1 && args[filesIndex + 1]) {
  options.files = args[filesIndex + 1].split(",").map((f) => f.trim());
}

const outputIndex = args.indexOf("--output");
if (outputIndex !== -1 && args[outputIndex + 1]) {
  options.outputPath = args[outputIndex + 1];
}

const API_KEY = process.env.GEMINI_API_KEY;

if (!API_KEY) {
  console.error("ERROR: GEMINI_API_KEY environment variable is required.");
  console.error("Set it with: export GEMINI_API_KEY=\"your-api-key\"");
  process.exit(1);
}

// Review prompts (same as WorkflowExperiment)
const SECURITY_REVIEW_PROMPT = `You are a senior security engineer conducting a thorough code review. 
Analyze the following code for security vulnerabilities and concerns.

Focus on:
1. Input validation and sanitization
2. SQL injection, XSS, and other injection attacks
3. Authentication and authorization issues
4. Sensitive data exposure
5. Path traversal vulnerabilities
6. Insecure dependencies or patterns
7. Error handling that exposes sensitive information
8. Hardcoded secrets or credentials

For each issue found, provide:
- Severity: CRITICAL, HIGH, MEDIUM, or LOW
- Location: File and approximate line/function
- Description: What the issue is
- Recommendation: How to fix it

If no security issues are found, confirm the code appears secure and note any security best practices observed.

Respond in JSON format:
{
  "summary": "Overall security assessment",
  "issues": [
    {
      "severity": "HIGH",
      "location": "file.py:functionName",
      "description": "Description of issue",
      "recommendation": "How to fix"
    }
  ],
  "positives": ["Good practices observed"],
  "overallRisk": "LOW|MEDIUM|HIGH|CRITICAL"
}`;

const QUALITY_REVIEW_PROMPT = `You are a senior software engineer conducting a code review.
Analyze the following code for quality, maintainability, and best practices.

Focus on:
1. Code clarity and readability
2. Error handling completeness
3. Edge case handling
4. Performance concerns
5. Code organization and modularity
6. Naming conventions
7. Documentation and comments
8. Potential bugs or logic errors
9. Test coverage considerations

For each issue found, provide:
- Priority: HIGH, MEDIUM, or LOW
- Location: File and approximate line/function
- Description: What the issue is
- Suggestion: How to improve

Respond in JSON format:
{
  "summary": "Overall code quality assessment",
  "issues": [
    {
      "priority": "MEDIUM",
      "location": "file.py:functionName",
      "description": "Description of issue",
      "suggestion": "How to improve"
    }
  ],
  "strengths": ["Good practices observed"],
  "overallQuality": "EXCELLENT|GOOD|ACCEPTABLE|NEEDS_WORK"
}`;

function getGitDiff() {
  try {
    let diff = "";
    try {
      diff = execSync("git diff HEAD", { encoding: "utf-8", maxBuffer: 1024 * 1024 });
    } catch (e) {
      diff = execSync("git diff --cached", { encoding: "utf-8", maxBuffer: 1024 * 1024 });
    }
    return diff || "No changes detected";
  } catch (error) {
    console.log("Git diff not available, will review specified files");
    return null;
  }
}

// Python project: walk src/ and tests/, skip .venv, __pycache__, etc.
function findSourceFiles(baseDir) {
  const files = [];
  const extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs"];
  const dirsToSkip = ["node_modules", ".venv", "venv", "__pycache__", ".ruff_cache", ".pytest_cache"];

  function walkDir(dir) {
    if (!fs.existsSync(dir)) return;

    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.name.startsWith(".") && entry.name !== ".cursor") continue;
      if (dirsToSkip.includes(entry.name)) continue;

      if (entry.isDirectory()) {
        walkDir(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (extensions.includes(ext)) {
          files.push(fullPath);
        }
      }
    }
  }

  const srcDir = path.join(baseDir, "src");
  const testsDir = path.join(baseDir, "tests");
  if (fs.existsSync(srcDir)) walkDir(srcDir);
  if (fs.existsSync(testsDir)) walkDir(testsDir);

  return files;
}

function readFilesContent(filePaths) {
  const contents = [];

  for (const filePath of filePaths) {
    try {
      let content = fs.readFileSync(filePath, "utf-8");
      if (content.length > MAX_FILE_SIZE) {
        content = content.substring(0, MAX_FILE_SIZE) + "\n\n... [truncated] ...";
      }
      contents.push({ path: filePath, content: content });
    } catch (error) {
      console.warn("Could not read " + filePath + ": " + error.message);
    }
  }

  return contents;
}

function buildCodeContext(files, diff) {
  let context = "";

  if (diff && options.useDiff) {
    context = "## Git Diff (Changes to Review)\n\n```diff\n" + diff + "\n```\n\n";
  }

  if (files.length > 0) {
    context += "## Source Files\n\n";
    for (const file of files) {
      const ext = path.extname(file.path).slice(1) || "text";
      context += "### " + file.path + "\n\n```" + ext + "\n" + file.content + "\n```\n\n";
    }
  }

  return context;
}

function callGemini(prompt, codeContext) {
  return new Promise((resolve, reject) => {
    const requestBody = JSON.stringify({
      contents: [
        {
          parts: [
            {
              text: prompt + "\n\n---\n\nCode to review:\n\n" + codeContext,
            },
          ],
        },
      ],
      generationConfig: {
        temperature: 0.2,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 8192,
      },
    });

    const requestOptions = {
      hostname: GEMINI_API_URL,
      port: 443,
      path: "/v1beta/models/" + GEMINI_MODEL + ":generateContent?key=" + API_KEY,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(requestBody),
      },
    };

    const req = https.request(requestOptions, (res) => {
      let data = "";

      res.on("data", (chunk) => {
        data += chunk;
      });

      res.on("end", () => {
        try {
          const response = JSON.parse(data);

          if (response.error) {
            reject(new Error("Gemini API error: " + response.error.message));
            return;
          }

          if (
            response.candidates &&
            response.candidates[0] &&
            response.candidates[0].content &&
            response.candidates[0].content.parts
          ) {
            const text = response.candidates[0].content.parts[0].text;
            resolve(text);
          } else {
            reject(new Error("Unexpected response format from Gemini"));
          }
        } catch (e) {
          reject(new Error("Failed to parse Gemini response: " + e.message));
        }
      });
    });

    req.on("error", (error) => {
      reject(new Error("Request failed: " + error.message));
    });

    req.write(requestBody);
    req.end();
  });
}

function parseGeminiResponse(response) {
  try {
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (e) {
    // ignore
  }

  return {
    summary: response,
    issues: [],
    raw: true,
  };
}

async function main() {
  console.log("=".repeat(60));
  console.log("AI CODE REVIEW (Gemini)");
  console.log("=".repeat(60));
  console.log("Timestamp: " + new Date().toISOString());
  console.log("Model: " + GEMINI_MODEL);
  console.log("");

  let filesToReview = [];
  let gitDiff = null;

  if (options.files.length > 0) {
    filesToReview = options.files;
    console.log("Reviewing specified files: " + filesToReview.join(", "));
  } else if (options.useDiff) {
    gitDiff = getGitDiff();
    if (!gitDiff || gitDiff === "No changes detected") {
      console.log("No git changes detected, reviewing src/ and tests/...");
      filesToReview = findSourceFiles(".");
    } else {
      console.log("Reviewing git diff...");
    }
  } else {
    filesToReview = findSourceFiles(".");
    console.log("Found " + filesToReview.length + " source files to review");
  }

  const fileContents = readFilesContent(filesToReview);
  const codeContext = buildCodeContext(fileContents, gitDiff);

  if (!codeContext || codeContext.trim().length < 50) {
    console.log("No code found to review.");
    process.exit(0);
  }

  console.log("\nCode context size: " + codeContext.length + " characters");

  const results = {
    timestamp: new Date().toISOString(),
    model: GEMINI_MODEL,
    filesReviewed: filesToReview,
    usedDiff: options.useDiff && !!gitDiff,
    securityReview: null,
    qualityReview: null,
    summary: {
      securityRisk: "UNKNOWN",
      codeQuality: "UNKNOWN",
      passesReview: false,
    },
  };

  console.log("\n" + "-".repeat(60));
  console.log("Running Security Review...");
  console.log("-".repeat(60));

  try {
    const securityResponse = await callGemini(SECURITY_REVIEW_PROMPT, codeContext);
    results.securityReview = parseGeminiResponse(securityResponse);

    if (results.securityReview.overallRisk) {
      results.summary.securityRisk = results.securityReview.overallRisk;
      console.log("Security Risk: " + results.securityReview.overallRisk);
    }

    if (results.securityReview.issues && results.securityReview.issues.length > 0) {
      console.log("Security Issues Found: " + results.securityReview.issues.length);
      for (const issue of results.securityReview.issues) {
        console.log("  [" + issue.severity + "] " + issue.location + ": " + issue.description);
      }
    } else {
      console.log("No security issues found.");
    }
  } catch (error) {
    console.error("Security review failed: " + error.message);
    results.securityReview = { error: error.message };
  }

  if (!options.securityFocus) {
    console.log("\n" + "-".repeat(60));
    console.log("Running Quality Review...");
    console.log("-".repeat(60));

    try {
      const qualityResponse = await callGemini(QUALITY_REVIEW_PROMPT, codeContext);
      results.qualityReview = parseGeminiResponse(qualityResponse);

      if (results.qualityReview.overallQuality) {
        results.summary.codeQuality = results.qualityReview.overallQuality;
        console.log("Code Quality: " + results.qualityReview.overallQuality);
      }

      if (results.qualityReview.issues && results.qualityReview.issues.length > 0) {
        console.log("Quality Issues Found: " + results.qualityReview.issues.length);
        for (const issue of results.qualityReview.issues) {
          console.log("  [" + issue.priority + "] " + issue.location + ": " + issue.description);
        }
      } else {
        console.log("No quality issues found.");
      }
    } catch (error) {
      console.error("Quality review failed: " + error.message);
      results.qualityReview = { error: error.message };
    }
  }

  const securityPass =
    !results.securityReview.overallRisk ||
    ["LOW", "MEDIUM"].includes(results.securityReview.overallRisk);
  const qualityPass =
    !results.qualityReview ||
    !results.qualityReview.overallQuality ||
    ["EXCELLENT", "GOOD", "ACCEPTABLE"].includes(results.qualityReview.overallQuality);

  results.summary.passesReview = securityPass && qualityPass;

  const outputDir = path.dirname(options.outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(options.outputPath, JSON.stringify(results, null, 2));

  console.log("\n" + "=".repeat(60));
  console.log("AI REVIEW SUMMARY");
  console.log("=".repeat(60));
  console.log("Security Risk:  " + results.summary.securityRisk);
  console.log("Code Quality:   " + results.summary.codeQuality);
  console.log("-".repeat(60));
  console.log("REVIEW RESULT:  " + (results.summary.passesReview ? "PASS" : "NEEDS ATTENTION"));
  console.log("=".repeat(60));
  console.log("\nReview results written to: " + options.outputPath);

  process.exit(results.summary.passesReview ? 0 : 1);
}

main().catch(function (error) {
  console.error("AI Review failed:", error);
  process.exit(1);
});
