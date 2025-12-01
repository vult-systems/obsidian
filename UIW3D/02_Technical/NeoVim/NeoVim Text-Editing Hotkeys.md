---

---
---
### Description
NeoVim is a keyboard extensive text-editor. The following will try to describe how to navigate, edit, delete, etc.  

---
## Navigation
```lua
----------------------------------
Move by character
h  ←   j  ↓   k  ↑   l  →
----------------------------------
Move by word
w   Go to next word start
e   Go to end of word
b   Go to previous word start
----------------------------------
Move to start / end of line
0   Start of line
$   End of line
----------------------------------
Move by paragraph / block
{   Up a block
}   Down a block
----------------------------------
```

---
## Insert Mode (Typing Mode)
```lua
----------------------------------
i   Insert before cursor
I   Insert at line start
a   Append after cursor
A   Append at end of line
o   Open new line below
O   Open new line above
----------------------------------
```

---
## Deleting Text
```lua
----------------------------------
x     Delete character under cursor
dw    Delete word
d$    Delete to end of line
dd    Delete entire line
d0    Delete to start of line
----------------------------------
```

---
## Copy & Paste (Yank and Put)
```lua
----------------------------------
yy    Yank (copy) whole line
yw    Yank word
p     Paste below/after
P     Paste above/before
----------------------------------
```

---
## Undo / Redo
```lua
----------------------------------
u     Undo
Ctrl+r  Redo
----------------------------------
```

---
## Change Operations (Delete + Enter Insert Mode)
```lua
----------------------------------
cw    Change word (delete word and go into insert mode)
c$    Change to end of line
cc    Change entire line
----------------------------------
```

---
## Visual Mode (Select Text)
```lua
----------------------------------
v     Character-wise select
V     Line-wise select
Ctrl+v  Block/column select
----------------------------------
```

Then run commands like:

```lua
----------------------------------
y   to copy
d   to delete
c   to change
<   indent left
>   indent right
----------------------------------
```

---
## Search
```lua
----------------------------------
/pattern      Search forward
?pattern      Search backward
n             Next match
N             Previous match
----------------------------------
```

---
## Indenting
```lua
----------------------------------
>>    Indent line
<<    Unindent line
==    Auto-indent line
----------------------------------
```

---
## Files & Buffers
```lua
----------------------------------
:w     Save
:q     Quit
:q!    Quit without saving
:wq    Save & quit
----------------------------------
```

---
# Config
~/.config/nvim/init.vim
~/.config/nvim/init.lua

```lua
----------------------------------
-- tabs vs spaces
vim.opt.tabstop = 2
vim.opt.expandtab = true
----------------------------------
```

---
Status
#Better

Related
[[What Is NeoVim]]

Tags
[[../../05_Utility/Tags/NeoVim|NeoVim]] [[../../05_Utility/Tags/Hotkeys|Hotkeys]]