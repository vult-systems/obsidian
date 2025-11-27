PowerShell is a command-line shell and a scripting language in one. Think of it as a bougee command prompt or terminal allowing for verbosity, automation, and more. 

It accepts and returns .NET objects, rather than text. These objects are an instance of a class that combine data (properties) and functions into a single unit, just like we see in OOP - which makes it easier to connect different commands in a *pipeline* as we can create, manipulate, and reuse those components. 

Shorthand: `pwsh`
File Type: `.ps1`

---
# Installation

Search for the latest version of PowerShell
```
winget search --id Microsoft.PowerShell
```

```
Name                   Id                               Version    Source
-------------------------------------------------------------------------
PowerShell             Microsoft.PowerShell             7.5.4.0    winget
PowerShell Preview     Microsoft.PowerShell.Preview     7.6.0.5    winget
```

Install PowerShell using the --id parameter
```
winget install --id Microsoft.PowerShell --source winget
```

Upgrade PowerShell if it's' available. 
```
winget upgrade --id Microsoft.PowerShell
```

---
# Using PowerShell
`cd`
	Change directory
`cd ..`
	Goes back a directory
`Set-Location -Path C:\`
	Goes to specific location, in this case `C:\`
	`Set-Location -Path C:\Repos` would set it to the `\Repos` folder.
`.\test.ps1`
	Executes the file written within that directory.

---
# **Cmdlet**
PowerShell comes with hundreds of preinstalled commands. PowerShell commands are called cmdlets - command lets. 

The name of each cmdlet consists of a *Verb-Noun* pair. For example, `Get-Process`. This naming convention makes it easier to understand what the cmdlet does. It also makes it easier to find the command you're looking for. When looking for a cmdlet to use, you can filter on the `Verb` or `Noun`.  

`Get-Command` 
	Showcases all cmdlet's loaded in the current PowerShell session. Too many to remember, however, knowing `Get-Command` will allow us to track down any we may need or may have forgotten. 

`Get-Command -noun Service`
	This will show all cmdlet's using the noun "Service".
	Output examples
		`Get-Service`
		`New-Service`
		`Remove-Service`

`Get-Help`
	Displays information about PowerShell commands and concepts. `Get-Help` first, then pass in whatever cmdlet you would like help with.  

`Get-Help Get-Service -Full`
	This will showcase things like:
		`Syntax`
		`Parameters`
		`Inputs`
		`Outputs`
		`Aliases`
			Short hand code. Probably not the play to use as it lacks verbosity which is why we'd want to use PowerShell in the first place. 
			`Get-Alias` would show all aliases and the cmdlets they would be used for. 
		`Remarks`

# Parameters



