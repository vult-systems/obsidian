---

---
---
### Description
A guide for setting up a Git repository for an Obsidian vault to be used cross platform. 

---
## Step 1: Navigate to Repository Root

```powershell
cd C:\Repos
```

This changes your current directory to the repository root where the `.git` folder lives.

---
## Step 2: Verify Git Repository Location

```powershell
Test-Path .git
```

`Test-Path` is a PowerShell cmdlet that checks if a file or folder exists. Returns `True` if found, `False` if not. This confirms you're in the correct Git repository root.

---
## Step 3: List Directory Contents

```powershell
ls
```

`ls` (alias for `Get-ChildItem`) lists the contents of the current directory. Shows you have an `Obsidian` folder.

---
## Step 4: Create .gitattributes File

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

 `@" ... "@` 
 PowerShell here-string syntax for multi-line text
- Everything between `@"` and `"@` is treated as literal text
- Preserves line breaks and formatting
- No need to escape special characters

`|` 
Pipe operator, sends output from left side to right side

`Out-File`
PowerShell cmdlet that writes content to a file

`-FilePath .gitattributes`
Specifies the filename to create

`-Encoding utf8` 
Ensures the file is saved as UTF-8 (Git standard)

All of this creates a `.gitattributes` file in `C:\Repos\.gitattributes`

---
## Step 5: Verify File Creation

```powershell
Get-Content .gitattributes
```

`Get-Content` reads and displays the contents of a file. This confirms the file was created correctly with all the content you specified.

---
## Step 6: Stage the File for Commit

```powershell
git add .gitattributes
```
 
---
## Step 7: Commit the Changes

```powershell
git commit -m "Init for my Obsidian notes with .gitatts for consistent line endings"
```

`git commit` 
Creates a snapshot of staged changes

`-m "message"` 
Add relevant notes to your git submission

---
## Step 8: Push Changes

```
git push
```

---
# PowerShell Concepts Used

## Cmdlets (Commands)

- **`Test-Path`** - Check if file/folder exists
- **`Get-ChildItem`** (alias: `ls`) - List directory contents
- **`Get-Content`** - Read file contents
- **`Out-File`** - Write content to a file

## Operators

- **`|`** (Pipe) - Send output from one command to another

## Syntax

- **`@" ... "@`** (Here-string) - Multi-line string literal
- **`-Parameter Value`** - Parameter syntax for cmdlets

## Parameters

- **`-FilePath`** - Specify file location
- **`-Encoding`** - Specify text encoding

---
Status
#Better Need to include .gitignore write up.

Related

Tags
[[../../05_Utility/Tags/Git|Git]] [[../../05_Utility/Tags/Obsidian|Obsidian]] [[../../05_Utility/Tags/Documentation|Documentation]] [[../../05_Utility/Tags/Learning|Learning]]