---

---
---
### Description
Fast installation guide using Windows Package Manager (winget).

---
# Install Git CLI

```powershell
winget install Git.Git
```

**Refresh your PATH:**

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

**Verify installation:**

```powershell
git --version
```

**Configure Git**: 

```powershell
git config --global user.name "vult-systems"
git config --global user.email "ops.vult@gmail.com"
```

---
# Install Obsidian

```powershell
winget install Obsidian.Obsidian
```

**Launch Obsidian:**

```powershell
Start-Process obsidian://
```

---
# One-Liner Installation (Both)

Install everything at once:

```powershell
winget install Git.Git Obsidian.Obsidian
```

Then refresh PATH and configure Git:

```powershell
# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Configure Git
git config --global user.name "vult-systems"
git config --global user.email "ops.vult@gmail.com"
```

---
# Verify Everything Works

```powershell
# Check Git
git --version

# Check Obsidian (opens the app)
Start-Process obsidian://
```


---
Status
#Good #Better #Best

Related
[[../../05_Utility/Proxies/Proxy Note|Proxy Note]]

Tags
[[../../05_Utility/Proxies/Proxy Tag|Proxy Tag]]