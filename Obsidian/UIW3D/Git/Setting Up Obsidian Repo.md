Documentation for setting up a Git repository for an Obsidian vault with proper line ending handling across Windows and macOS platforms.

---
### Step 1: Navigate to Repository Root

```powershell
cd C:\Repos
```

**What this does:** Changes your current directory to the repository root where the `.git` folder lives.

---
### Step 2: Verify Git Repository Location

```powershell
Test-Path .git
```

**Output:** `True`

**What this does:** `Test-Path` is a PowerShell cmdlet that checks if a file or folder exists. Returns `True` if found, `False` if not. This confirms you're in the correct Git repository root.

---
### Step 3: List Directory Contents

```powershell
ls
```

**Output:**

```
Directory: C:\Repos
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          11/26/2025  6:37 PM                Obsidian
```

**What this does:** `ls` (alias for `Get-ChildItem`) lists the contents of the current directory. Shows you have an `Obsidian` folder.

---
### Step 4: Create .gitattributes File

```powershell
@"
# Auto detect text files and perform LF normalization
* text=auto

# Normalize and convert the listed file types to native line endings
*.md text
*.json text
*.js text

# Files that will have CRLF line endings
*.bat text eol=crlf

# Files that are truly binary and should not be modified
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pdf binary
"@ | Out-File -FilePath .gitattributes -Encoding utf8
```

**What this does:**

- **`@" ... "@`** - PowerShell here-string syntax for multi-line text
    - Everything between `@"` and `"@` is treated as literal text
    - Preserves line breaks and formatting
    - No need to escape special characters
- **`|`** - Pipe operator, sends output from left side to right side
- **`Out-File`** - PowerShell cmdlet that writes content to a file
    - `-FilePath .gitattributes` - specifies the filename to create
    - `-Encoding utf8` - ensures the file is saved as UTF-8 (Git standard)

**Result:** Creates a `.gitattributes` file in `C:\Repos\.gitattributes`

---
### Step 5: Verify File Creation

```powershell
Get-Content .gitattributes
```

**What this does:** `Get-Content` reads and displays the contents of a file. This confirms the file was created correctly with all the content you specified.

**Note:** You initially typed `.gitattributres` (typo) which caused an error. PowerShell is case-sensitive for paths and exact spelling matters.

---
### Step 6: Stage the File for Commit

```powershell
git add .gitattributes
```

**Output:**

```
warning: in the working copy of '.gitattributes', LF will be replaced by CRLF the next time Git touches it
```

**What this does:**

- `git add` stages files for the next commit
- The warning is informational - Git is converting line endings as configured
- Your prompt changes from `+16` to `+17` (17 files now staged)

---
### Step 7: Check Repository Status

```powershell
git status
```

**Output:**

```
On branch master
No commits yet
Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitattributes
        new file:   Obsidian/UIW3D/.obsidian/app.json
        [... 15 more files ...]
```

**What this does:** Shows the current state of your repository:

- Which branch you're on (`master`)
- What files are staged for commit (green, "Changes to be committed")
- What files are modified but not staged (red, "Changes not staged")
- What files are untracked (red, "Untracked files")

---
### Step 8: Commit the Changes

```powershell
git commit -m "Init for my Obsidian notes with .gitatts for consistent line endings"
```

**Output:**

```
[master (root-commit) bbf9492] Init for my Obsidian notes with .gitatts for consistent line endings
 17 files changed, 9495 insertions(+)
 create mode 100644 .gitattributes
 [... list of all 17 files created ...]
```

**What this does:**

- `git commit` creates a snapshot of staged changes
- `-m "message"` adds a commit message inline (without opening an editor)
- `(root-commit)` indicates this is the first commit in the repository
- `bbf9492` is the commit hash (unique identifier)
- Shows 17 files changed with 9,495 lines added

**Result:** Your prompt changes from `master ≢ +17` to `master ≢` - meaning you're on master branch with no uncommitted changes.

---
## PowerShell Concepts You Used

### Cmdlets (Commands)

- **`Test-Path`** - Check if file/folder exists
- **`Get-ChildItem`** (alias: `ls`) - List directory contents
- **`Get-Content`** - Read file contents
- **`Out-File`** - Write content to a file

### Operators

- **`|`** (Pipe) - Send output from one command to another

### Syntax

- **`@" ... "@`** (Here-string) - Multi-line string literal
- **`-Parameter Value`** - Parameter syntax for cmdlets

### Parameters

- **`-FilePath`** - Specify file location
- **`-Encoding`** - Specify text encoding

---
## Git Commands You Used

- **`git add <file>`** - Stage files for commit
- **`git status`** - Check repository state
- **`git commit -m "message"`** - Create a commit with a message

---
## Key Takeaways

1. **Here-strings** (`@" ... "@`) are perfect for creating multi-line configuration files
2. **Piping** (`|`) lets you chain commands together - output of one becomes input of another
3. **`Test-Path`** is your friend for verifying locations before operations
4. **Git warnings** about line endings are informational when you have `.gitattributes` configured
5. **PowerShell aliases** like `ls` make it feel familiar if you know Unix commands, but they're calling PowerShell cmdlets underneath

This workflow is now repeatable for any future Git operations in your Obsidian vault!

---
Related: [[../PowerShell/What is PowerShell|What is PowerShell]]

---
Tags: #Obsidian #Git #PowerShell #Documenation

