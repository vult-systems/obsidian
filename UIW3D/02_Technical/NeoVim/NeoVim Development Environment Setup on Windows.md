---

---
---
## Description
My mac development setup is getting dialed in and this is an attempt to replicate it on my Windows machine.

---
# Part 1: Font Installation
---
Download and install your preferred **Nerd Font: 

```cardlink
url: https://www.nerdfonts.com/font-downloads
title: "Nerd Fonts - Iconic font aggregator, glyphs/icons collection, & fonts patcher"
description: "Iconic font aggregator, collection, & patcher: 9,000+ glyph/icons, 60+ patched fonts: Hack, Source Code Pro, more. Popular glyph collections: Font Awesome, Octicons, Material Design Icons, and more"
host: www.nerdfonts.com
image: https://www.nerdfonts.com/assets/img/sankey-glyphs-combined-diagram.png
```

 **Configure Windows Terminal:**
    - Open Windows Terminal/PowerShell
    - Go to: `Settings → Profiles → Defaults → Appearance`
    - Set **Font face** to your installed Nerd Font

---
## Recommended Fonts
- [Fixedsys1984 — Travis Owens](https://www.programmingfonts.org/#fixedsys)
- [Fixedsys with Ligatures2016 — Darien Valentine](https://www.programmingfonts.org/#fixedsys-ligatures)
- [GNU Unifont1998 — Roman Czyborra](https://www.programmingfonts.org/#unifont)
- [Gohufont 142010 — Hugo Chargois](https://www.programmingfonts.org/#gohufont-14)
- [IBM VGA 9x161987 — IBM](https://www.programmingfonts.org/#ibm-vga)
- [Proggy Clean2004 — Tristan Grimmer](https://www.programmingfonts.org/#proggy-clean)
- [Scientifica2019 — Akshay Oppiliappan](https://www.programmingfonts.org/#scientifica)
- [UnifontEX2023 — stgiga](https://www.programmingfonts.org/#unifontex)
- [VT3232014 — Peter Hull](https://www.programmingfonts.org/#vt323)

---
# Part 2: Configure PowerShell
---
## Step 1: Create Your Profile

Check if you have a profile:

```powershell
Test-Path $PROFILE
```

IIf it returns `False`, create it:

```powershell
New-Item -ItemType File -Force -Path $PROFILE
```

### Step 2: Add Custom Functions

Open your profile:

```powershell
notepad $PROFILE
```

Paste this configuration:

```powershell
# Add local bin to PATH
$env:PATH += ";$HOME\.local\bin"

# PSReadLine options for better IntelliSense
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView
Set-PSReadLineOption -EditMode Windows

# Menu completion for Tab (shows folder list for cd, etc.)
Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete

# Show tooltips during completion
Set-PSReadLineOption -ShowToolTips

# Bell/visual feedback when commands complete
Set-PSReadLineOption -BellStyle Visual

# Show last command status more clearly
$PSStyle.Formatting.Error = "`e[91m"  # Bright red for errors
```

**What this does:**

- Adds `~/.local/bin` to your PATH (like Linux/macOS)
- Creates `hist` command to search your command history

---
### Step 3: Load Your New Profile

```powershell
. $PROFILE
```

**Test it**: Try typing hist git to search your history!

---
# Part 3: Install and Configure Neovim

### Step 1: Install Neovim

```powershell
winget install Neovim.Neovim
```

Wait for installation to complete, then **refresh your PATH**:

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

**Verify installation:**

```powershell
nvim --version
```

You should see: `NVIM v0.11.5` (or similar)

---

### Step 2: Set Up Directory Structure

Create the config directory:

```powershell
New-Item -ItemType Directory -Force -Path "$env:LOCALAPPDATA\nvim"
```

---

### Step 3: Install Kanagawa Theme

```powershell
git clone https://github.com/rebelot/kanagawa.nvim.git "$env:LOCALAPPDATA\nvim-data\site\pack\plugins\start\kanagawa.nvim"
```

---
### Step 4: Create Your Configuration File

Navigate to your config directory:

```powershell
cd "$env:LOCALAPPDATA\nvim"
```

Create `init.lua` using:

```
nvim init.lua
```

Copy and paste this into the file:

```lua
-- Leader key: space
vim.g.mapleader = ' '

-- Line numbers
vim.o.number = true
vim.o.relativenumber = true

-- Clipboard sync with Windows
vim.api.nvim_create_autocmd('UIEnter', {
  callback = function()
    vim.o.clipboard = 'unnamedplus'
  end,
})

-- Smart case-insensitive search
vim.o.ignorecase = true
vim.o.smartcase = true

-- Visual helpers
vim.o.cursorcolumn = true
vim.o.scrolloff = 10
vim.o.list = true
vim.o.confirm = true

-- Exit terminal mode with Esc
vim.keymap.set('t', '<Esc>', '<C-\\><C-n>')

-- Window navigation with Alt + hjkl
vim.keymap.set({ 't', 'i' }, '<A-h>', '<C-\\><C-n><C-w>h')
vim.keymap.set({ 't', 'i' }, '<A-j>', '<C-\\><C-n><C-w>j')
vim.keymap.set({ 't', 'i' }, '<A-k>', '<C-\\><C-n><C-w>k')
vim.keymap.set({ 't', 'i' }, '<A-l>', '<C-\\><C-n><C-w>l')
vim.keymap.set({ 'n' }, '<A-h>', '<C-w>h')
vim.keymap.set({ 'n' }, '<A-j>', '<C-w>j')
vim.keymap.set({ 'n' }, '<A-k>', '<C-w>k')
vim.keymap.set({ 'n' }, '<A-l>', '<C-w>l')

-- Highlight yanked text
vim.api.nvim_create_autocmd('TextYankPost', {
  desc = 'Highlight when yanking text',
  callback = function()
    vim.hl.on_yank()
  end,
})

-- Git blame command
vim.api.nvim_create_user_command('GitBlameLine', function()
  local line_number = vim.fn.line('.')
  local filename = vim.api.nvim_buf_get_name(0)
  print(vim.fn.system({ 'git', 'blame', '-L', line_number .. ',+1', filename }))
end, { desc = 'Show git blame for current line' })

-- Optional packages
vim.cmd('packadd! nohlsearch')

-- Kanagawa Dragon Theme
vim.opt.termguicolors = true
vim.cmd('colorscheme kanagawa-dragon')

-- PowerShell integration (Windows)
if vim.fn.has('win32') == 1 then
  vim.opt.shell = 'pwsh'
  vim.opt.shellcmdflag = '-NoLogo -NoProfile -ExecutionPolicy RemoteSigned -Command [Console]::InputEncoding=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;'
  vim.opt.shellredir = '2>&1 | Out-File -Encoding UTF8 %s; exit `$LastExitCode'
  vim.opt.shellpipe = '2>&1 | Out-File -Encoding UTF8 %s; exit `$LastExitCode'
  vim.opt.shellquote = ''
  vim.opt.shellxquote = ''
end
```

**What this config provides:**

-  Kanagawa Dragon theme (dark, professional colors)
-  Line numbers and relative line numbers
-  Windows clipboard integration
-  Alt+hjkl for window navigation
-  PowerShell support (run `ls`, `pwd`, etc. in Neovim)
-  Git blame command (`:GitBlameLine`)

---
### Step 5: Test Your Setup

Launch Neovim:

```powershell
nvim
```

**You should see:**

- Dark Kanagawa Dragon theme
- Line numbers on the left
- No errors

**Test PowerShell commands:** Inside Neovim, try:

```vim
:!ls
:!pwd
:!git status
```

These should all work!

**Exit Neovim:** Press `Esc` then type `:q` and press `Enter`

---
##  Updating the Theme

When theme updates are available:

```powershell
cd "$env:LOCALAPPDATA\nvim-data\site\pack\plugins\start\kanagawa.nvim"
git pull
```

Restart Neovim to see changes.

---
##  File Locations

| Item               | Location                                                         |
| ------------------ | ---------------------------------------------------------------- |
| Neovim config      | `%LOCALAPPDATA%\nvim\init.lua`                                   |
| Theme plugin       | `%LOCALAPPDATA%\nvim-data\site\pack\plugins\start\kanagawa.nvim` |
| PowerShell profile | `$PROFILE` (varies by user)                                      |

**Quick navigation:**

```powershell
# Open config
nvim "$env:LOCALAPPDATA\nvim\init.lua"

# Open PowerShell profile
nvim $PROFILE

# Go to theme directory
cd "$env:LOCALAPPDATA\nvim-data\site\pack\plugins\start\kanagawa.nvim"
```

---
Status
#Better

Related
[[What Is NeoVim|What Is NeoVim]] [[NeoVim Text-Editing Hotkeys|NeoVim Text-Editing Hotkeys]]

Tags
[[../../05_Utility/Tags/NeoVim|NeoVim]] [[../../05_Utility/Tags/PowerShell|PowerShell]] [[../../05_Utility/Tags/Documentation|Documentation]] [[../../05_Utility/Tags/Command Line|Command Line]] [[../../05_Utility/Tags/Resources|Resources]] 