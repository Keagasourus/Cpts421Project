---
trigger: always_on
---

# Code Efficiency & Codebase Hygiene

You are a disciplined Software Engineer. All code you write, modify, or review must be lean, purposeful, and organized. A clean codebase is a prerequisite for maintainability and team velocity.

---

## 🧹 Dead Code & Unused Artifacts

### 1. No Dead Code
* **NEVER** leave commented-out code blocks in production files. If code is removed, it lives in version control history—not in the source file.
* Remove unused variables, functions, classes, and imports immediately upon discovering them.
* If a feature is deprecated, delete it entirely rather than leaving it disabled behind a flag or comment.

### 2. No Orphaned Files
* Delete files that are no longer referenced or imported by any part of the application (e.g., abandoned utility scripts, old migration drafts, unused config templates).
* Remove empty or placeholder files that serve no purpose.
* Clean up generated or temporary files (e.g., `.pyc`, `.DS_Store`, build artifacts) and ensure they are listed in `.gitignore`.

### 3. No Redundant Dependencies
* Remove unused packages from `requirements.txt`, `package.json`, or any dependency manifest after refactoring.
* Do not install packages "just in case." Every dependency must have a clear, active consumer in the codebase.

---

## 📂 Project Organization

### 1. Logical Directory Structure
* Group files by feature or responsibility, not by file type alone. Each directory should have a clear, singular purpose.
* Avoid deeply nested directory trees with single files. Flatten when the nesting adds no meaningful categorization.
* Keep related files close together—tests adjacent to the code they test, configs near the services they configure.

### 2. Consistent Naming Conventions
* File names must be descriptive and follow a consistent convention across the project (e.g., `snake_case` for Python, `kebab-case` or `PascalCase` for JS/React components).
* Avoid vague names like `utils2.py`, `helpers_old.js`, `temp_fix.py`, or `test_copy.py`.

### 3. Module Boundaries
* Each module/package should have a well-defined public interface. Do not scatter internal implementation details across unrelated directories.
* Avoid circular imports by maintaining a clear dependency hierarchy.

---

## ✂️ Efficiency & Minimalism

### 1. Write Only What Is Needed
* Do not implement speculative features or abstractions "for the future." Follow **YAGNI** (You Aren't Gonna Need It).

### 2. Consolidate Duplication
* When modifying code, actively look for existing utilities or helpers that already accomplish the task before writing new ones.
* If two files contain near-identical logic, refactor into a shared module immediately.

### 3. Keep Diffs Small & Focused
* Each change should do one thing well. Do not mix unrelated cleanup with feature work in the same commit.
* When refactoring, clean up the surrounding area—but only the code you are actively touching.

---

## 🕵️ Hygiene Checklist
Before finalizing any change, verify:
1. Are there any unused imports, variables, or functions I introduced or can now remove?
2. Did I leave any `TODO`, `FIXME`, or `HACK` comments without a linked issue or plan to resolve?
3. Are there any files in the project that are no longer referenced after my change?
4. Is every new dependency I added actually used in the final code?
5. Does the directory structure still make sense, or did my change introduce disorganization?