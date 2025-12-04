  Create a setup script to run on all worker machines:

  # Setup-ArnoldCache.ps1
  $cacheDir = "D:\ArnoldCache\tx"

  # Create cache directory
  New-Item -Path $cacheDir -ItemType Directory -Force

  # Set environment variable
  [System.Environment]::SetEnvironmentVariable(
      'ARNOLD_TEXTURE_CACHE_DIR',
      $cacheDir,
      'Machine'
  )

  # Grant permissions to all csadmin accounts
  @("csadmin400", "csadmin405", "csadmin406", "csadmin407") | ForEach-Object {
      icacls $cacheDir /grant "${_}:(OI)(CI)F" /T
  }

  Write-Host "✓ Arnold texture cache configured at: $cacheDir" -ForegroundColor Green

  # Restart Deadline service
  Restart-Service -Name "DeadlineLauncher10"
  Write-Host "✓ Deadline service restarted" -ForegroundColor Green
