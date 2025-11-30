---

---
---
### Description
The command and explanation for opening my Obsidian notes (UIW3D vault) via PowerShell. 

---
## Open Obsidian via PowerShell

``` PowerShell
Start-Process "obsidian://open?vault=UIW3D"
```

---
### PowerShell Cmdlet

`Start-Process`
A PowerShell **cmdlet** that launches a process, application, or URL. 
- PowerShell uses this to open executables, documents, or registered URL protocols. 

---
### Obsidian Protocol
Obsidian registers the `obsidian://` protocol with Windows when installed, so PowerShell or your browser can call Obsidian through URLs. 

`obsidian://`
- Custom **protocol** scheme for Obsidian
- Tells Windows: "Pass this request to Obsidian"

	``open`
	- The **action (endpoint)** you want Obsidian to perform. 
	- `open` tells Obsidian to open a vault or a specific note.`
	
	`?`
	This marks where the parameter begins. In URL syntax:
	- Everything before the `?` is the **base action** or **endpoint**
	- Everything after the `?` is a **list** or **parameters** you're passing to that action. 
	
	`vault=UIW3D`
	- The **parameter** telling Obsidian which vault to open. 
	- Each `key=value` pair is a parameter. The first one starts after a `?` and additional ones use `&`
		- Additional examples include: 
			- `open?vault=UIW3D&file=Notes/PowerShell.md`
			- `search?vault=UIW3D&query=pipeline`

---
Status 
#Best

Related
[[What is PowerShell|What is PowerShell]] 

Tags
[[../../05_Utility/Tags/PowerShell|PowerShell]] [[../../05_Utility/Tags/Documentation|Documentation]] [[../../05_Utility/Tags/Obsidian|Obsidian]]