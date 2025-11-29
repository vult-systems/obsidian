---

---
---
**Status** #Best

**Related**
[[What is PowerShell|What is PowerShell]]

**Tags**
[[../../03_Utility/Tags/Git|Git]] [[../../03_Utility/Tags/Obsidian|Obsidian]] [[../../03_Utility/Tags/Documentation|Documentation]] [[../../03_Utility/Tags/PowerShell|PowerShell]] [[../../03_Utility/Tags/Automation|Automation]]

---
### Description
A PowerShell automation script that streamlines the Git workflow by combining `git add`, `git commit`, and `git push` operations into a single command `obsync`

---
### Assumptions

- PowerShell 7+ (`pwsh`)
- Git installed and configured
- Obsidian vault initialized as a Git repository
- GitHub repository set up as remote

---
## Step 1: Create the Script Directory

```powershell
mkdir C:\Scripts
```

---
## Step 2: Create the Sync Script

```
nvim Sync-Obsdian.ps1
```

This creates the PowerShell script using NeoVim. 

```powershell
# Git Sync Script Using PowerShell Automation

param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

# Change to Obsidian repo
Set-Location C:\Repos\obsidian

# Show current status
Write-Host "`n=== Current Changes ===" -ForegroundColor Yellow
git status --short

# Check if there are changes
$changes = git status --short
if ([string]::IsNullOrWhiteSpace($changes)) {
    Write-Host "`nNo changes to commit." -ForegroundColor Green
    exit
}

# Confirm before proceeding
Write-Host ""
$confirm = Read-Host "Proceed with sync? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Host "Sync cancelled." -ForegroundColor Red
    exit
}

# Stage all changes
Write-Host "`n[1/3] Staging changes..." -ForegroundColor Cyan
git add .

# Commit with message
Write-Host "[2/3] Committing: '$Message'" -ForegroundColor Cyan
git commit -m $Message

# Push to remote
Write-Host "[3/3] Pushing to GitHub..." -ForegroundColor Cyan
git push

Write-Host "`n Sync complete!" -ForegroundColor Green
```

---
## Step 3: Add Alias to PowerShell Profile

Open your PowerShell profile:
```powershell
nvim $PROFILE
```

Add these lines:
```powershell
# Obsidian Git Sync Alias
function Sync-Obsidian { C:\Scripts\Sync-Obsidian.ps1 @args }
Set-Alias obsync Sync-Obsidian
```

---
## Step 4: Reload Profile
```powershell
. $PROFILE
```

---
## Step 5: Use The Script

```powershell
obsync "Your commit message here"
```

---
# How It Works

## Parameters
`-Message`
- Required, Type: String
- The commit message describing whats changes
## Script Behavior
**Change Detection**
- `git status --short` 
	- This runs to display pending changes
- Exits gracefully if no changes detected

**Safety Confirmation**
- Prompts user to confirm before syncing
- Prevents accidental commits

**Progress Feedback**
- Color-coded output for each step
- Clear success/failure messages

---
## Simplified Script

```powershell
# 1. Navigate to repo
Set-Location C:\Repos\obsidian

# 2. Check for changes
git status --short

# 3. Stage everything
git add .

# 4. Commit with message
git commit -m $Message

# 5. Push to remote
git push
```

---
## Customization

### Change Repository Path

Edit line 16 in the script:
```powershell
Set-Location C:\Repos\obsidian  # Change this path
```

### Change Alias Name

In your `$PROFILE`, modify the alias:
```powershell
Set-Alias obsync Sync-Obsidian  # Use any name you want
```

### Add Auto-Pull Before Sync

Add this after line 16:
```powershell
# Pull latest changes first
Write-Host "Pulling latest changes..." -ForegroundColor Cyan
git pull
```


---
# Troubleshooting

### "Script not found" Error

**Problem:** PowerShell can't find the script.

**Solution:** Verify the script exists:
```powershell
Test-Path C:\Scripts\Sync-Obsidian.ps1
```

### "Cannot be loaded because running scripts is disabled"

**Problem:** PowerShell execution policy blocks scripts.

**Solution:** Set execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Alias not working after profile edit

**Problem:** Profile not reloaded.

**Solution:** Reload your profile:
```powershell
. $PROFILE
```

### Git authentication errors

**Problem:** GitHub credentials not configured.

**Solution:** Authenticate with GitHub CLI:
```powershell
gh auth login
```

---
# macOS/Linux Version

For cross-platform use, create `~/Scripts/sync-obsidian.sh`:

```bash
#!/bin/bash

# Quick Git sync for Obsidian vault
MESSAGE="$1"

if [ -z "$MESSAGE" ]; then
    echo "Error: Commit message required"
    echo "Usage: obsync \"Your message here\""
    exit 1
fi

cd ~/Repos/obsidian

echo -e "\n=== Current Changes ==="
git status --short

if [ -z "$(git status --short)" ]; then
    echo -e "\nNo changes to commit."
    exit 0
fi

read -p $'\nProceed with sync? (Y/N): ' confirm
if [ "$confirm" != "Y" ] && [ "$confirm" != "y" ]; then
    echo "Sync cancelled."
    exit 0
fi

echo -e "\n[1/3] Staging changes..."
git add .

echo "[2/3] Committing: '$MESSAGE'"
git commit -m "$MESSAGE"

echo "[3/3] Pushing to GitHub..."
git push

echo -e "\n Sync complete!"
```

Make executable and add alias:

```bash
chmod +x ~/Scripts/sync-obsidian.sh
echo 'alias obsync="~/Scripts/sync-obsidian.sh"' >> ~/.zshrc
source ~/.zshrc
```