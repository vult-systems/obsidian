# What is PowerShell?

PowerShell is a command-line shell and scripting language combined into one powerful tool. Think of it as an advanced command prompt that enables verbosity, automation, and system management at scale.

## Key Characteristics

**Object-Based Processing**
- PowerShell accepts and returns .NET objects rather than plain text
- Objects are instances of classes that combine data (properties) and functions (methods) into a single unit
- This object-oriented approach makes it easier to connect commands in a *pipeline*
- You can create, manipulate, and reuse components efficiently

**Quick Reference**
- Shorthand: `pwsh`
- File Extension: `.ps1`

---

## Installation

### Search for Latest Version
```powershell
winget search --id Microsoft.PowerShell
```

**Output:**
```
Name                   Id                               Version    Source
-------------------------------------------------------------------------
PowerShell             Microsoft.PowerShell             7.5.4.0    winget
PowerShell Preview     Microsoft.PowerShell.Preview     7.6.0.5    winget
```

### Install PowerShell
```powershell
winget install --id Microsoft.PowerShell --source winget
```

### Upgrade PowerShell
```powershell
winget upgrade --id Microsoft.PowerShell
```

---

## Basic Navigation Commands

**Change Directory**
```powershell
cd C:\Users
```

**Go Back One Directory**
```powershell
cd ..
```

**Set Specific Location**
```powershell
Set-Location -Path C:\Repos
```

**Execute a Script**
```powershell
.\test.ps1
```
*Note: Script must be in current directory*

---

## Cmdlets (Command-lets)

PowerShell commands are called **cmdlets** and follow a consistent `Verb-Noun` naming convention. This structure makes commands intuitive and discoverable.

### Finding Commands

**List All Available Cmdlets**
```powershell
Get-Command
```
*Shows all cmdlets loaded in the current PowerShell session*

**Filter by Noun**
```powershell
Get-Command -Noun Service
```

**Example Output:**
- `Get-Service` - Retrieves services
- `New-Service` - Creates a new service
- `Remove-Service` - Deletes a service
- `Restart-Service` - Restarts a service

**Filter by Verb**
```powershell
Get-Command -Verb Get
```
*Shows all cmdlets that retrieve information*

---

## Getting Help

**Display Help for Any Cmdlet**
```powershell
Get-Help <cmdlet-name>
```

**Full Detailed Help**
```powershell
Get-Help Get-Service -Full
```

**Help Contents Include:**
- **Syntax** - How to structure the command
- **Parameters** - Available options and flags
- **Inputs** - What the cmdlet accepts
- **Outputs** - What the cmdlet returns
- **Aliases** - Shorthand alternatives
- **Examples** - Practical usage scenarios
- **Remarks** - Additional notes and tips

**Update Help Documentation**
```powershell
Update-Help
```
*Downloads the latest help files from Microsoft*

---

## Parameters

Parameters modify how cmdlets behave and allow you to specify options. They're preceded by a hyphen (`-`).

**Syntax:**
```powershell
Cmdlet-Name -ParameterName Value
```

**Examples:**
```powershell
Get-Service -Name "wuauserv"
Get-ChildItem -Path C:\Repos -Recurse
Set-Location -Path C:\Users
```

---

## Aliases

Aliases are shorthand versions of cmdlets. While convenient for interactive use, they sacrifice the verbosity that makes PowerShell scripts readable and maintainable.

**View All Aliases**
```powershell
Get-Alias
```

**Common Examples:**
- `ls` → `Get-ChildItem`
- `cd` → `Set-Location`
- `cls` → `Clear-Host`
- `cat` → `Get-Content`

**Best Practice:** Use full cmdlet names in scripts for clarity and maintainability. Save aliases for interactive terminal use only.

---

## Why PowerShell?

- **Automation** - Script repetitive tasks
- **Consistency** - Verb-Noun naming convention
- **Discoverability** - Easy to find and learn commands
- **Object Pipeline** - Pass rich data between commands
- **Cross-Platform** - Runs on Windows, macOS, and Linux
- **Integration** - Deep system access and .NET framework support

---

**Related:** [[Git Setup for Obsidian]]

**Tags:** #PowerShell #Documentation #Basics #CommandLine