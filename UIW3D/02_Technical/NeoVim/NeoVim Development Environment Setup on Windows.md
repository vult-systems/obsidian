## Description
This is my current NeoVim setup and configuration below. I'm using the `init.lua` template from the `:Tutor` lesson. I slightly tweaked it, but I need to deep dive the configuration setting in order to fully customize it. I will continue to update this write-up and documentation as I go.  

---
# Step-By-Step Guide
---
## Step 1: Install Neovim

```powershell
winget install Neovim.Neovim
```

Restart your terminal after installation.

---
## Step 2: Create Config Directory

```powershell
New-Item -ItemType Directory -Force -Path "$env:LOCALAPPDATA\nvim"
```

---
## Step 3: Install Kanagawa Theme

```powershell
git clone https://github.com/rebelot/kanagawa.nvim.git "$env:LOCALAPPDATA\nvim-data\site\pack\plugins\start\kanagawa.nvim"
```

---
## Step 4: Create init.lua
Find or edit the `init.lua` nvim configuration file or create it.
The file can be found, edited, or created 

- `%LOCALAPPDATA%\nvim\init.lua`
- `~/.config/nvim/initl.lua` 

Copy and paste the follow code below, then save the file.

```lua
-- Set <space> as the leader key
vim.g.mapleader = ' '

-- Print the line number in front of each line
vim.o.number = true
vim.cmd("colorscheme kanagawa-dragon")

-- Use relative line numbers, so that it is easier to jump with j, k. This will affect the 'number'
-- option above, see `:h number_relativenumber`
vim.o.relativenumber = true

-- Sync clipboard between OS and Neovim.
vim.api.nvim_create_autocmd('UIEnter', {
callback = function()
vim.o.clipboard = 'unnamedplus'
end,
})

-- Case-insensitive searching UNLESS \C or one or more capital letters in the search term
vim.o.ignorecase = true
vim.o.smartcase = true

-- Highlight the line where the cursor is on
-- vim.o.cursorline = true
vim.o.cursorcolumn = true
  
-- Minimal number of screen lines to keep above and below the cursor.
vim.o.scrolloff = 10

-- Show <tab> and trailing spaces
vim.o.list = true

-- if performing an operation that would fail due to unsaved changes in the buffer (like `:q`),
-- instead raise a dialog asking if you wish to save the current file(s) See `:help 'confirm'`
vim.o.confirm = true

-- [[ Set up keymaps ]] See `:h vim.keymap.set()`, `:h mapping`, `:h keycodes`
-- Use <Esc> to exit terminal mode
vim.keymap.set('t', '<Esc>', '<C-\\><C-n>')

-- Map <A-j>, <A-k>, <A-h>, <A-l> to navigate between windows in any modes
vim.keymap.set({ 't', 'i' }, '<A-h>', '<C-\\><C-n><C-w>h')
vim.keymap.set({ 't', 'i' }, '<A-j>', '<C-\\><C-n><C-w>j')
vim.keymap.set({ 't', 'i' }, '<A-k>', '<C-\\><C-n><C-w>k')
vim.keymap.set({ 't', 'i' }, '<A-l>', '<C-\\><C-n><C-w>l')
vim.keymap.set({ 'n' }, '<A-h>', '<C-w>h')
vim.keymap.set({ 'n' }, '<A-j>', '<C-w>j')
vim.keymap.set({ 'n' }, '<A-k>', '<C-w>k')
vim.keymap.set({ 'n' }, '<A-l>', '<C-w>l')

-- [[ Basic Autocommands ]].
-- See `:h lua-guide-autocommands`, `:h autocmd`, `:h nvim_create_autocmd()`

-- Highlight when yanking (copying) text.
-- Try it with `yap` in normal mode. See `:h vim.hl.on_yank()`
vim.api.nvim_create_autocmd('TextYankPost', {
desc = 'Highlight when yanking (copying) text',
callback = function()
vim.hl.on_yank()
end,
})
  
-- [[ Create user commands ]]
-- See `:h nvim_create_user_command()` and `:h user-commands`
  
-- Create a command `:GitBlameLine` that print the git blame for the current line
vim.api.nvim_create_user_command('GitBlameLine', function()
local line_number = vim.fn.line('.') -- Get the current line number. See `:h line()`
local filename = vim.api.nvim_buf_get_name(0)
print(vim.fn.system({ 'git', 'blame', '-L', line_number .. ',+1', filename }))
end, { desc = 'Print the git blame for the current line' })

-- [[ Add optional packages ]]
-- Nvim comes bundled with a set of packages that are not enabled by
-- default. You can enable any of them by using the `:packadd` command.
  
-- For example, to add the "nohlsearch" package to automatically turn off search highlighting after
-- 'updatetime' and when going to insert mode
vim.cmd('packadd! nohlsearch')
  
-- Kanagawa Theme Plugin located here: ~/.local/share/nvim/site/pack/plugins/start/kanagawa.nvim
-- To update run the following:
-- cd ~/.local/share/nvim/site/pack/plugins/start/kanagawa.nvim
-- git pull
vim.opt.termguicolors = true
vim.cmd("colorscheme kanagawa-dragon")
```

---
## Step 5: Verify
Launch Neovim:

```powershell
nvim
```

The Kanagawa Dragon theme should now be active.

---
# Updating the Theme
As needed you can update the theme by pulling from the source branch hosted on git. 

```powershell
cd "$env:LOCALAPPDATA\nvim-data\site\pack\plugins\start\kanagawa.nvim"
git pull
```

---
Status
#Good 

Related
[[What Is NeoVim|What Is NeoVim]] [[NeoVim Text-Editing Hotkeys|NeoVim Text-Editing Hotkeys]]

Tags
[[../../05_Utility/Tags/NeoVim|NeoVim]] 