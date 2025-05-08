# Define the target directory
$targetDir = "A:\Dev\Games\TheSimpsonsGame\GameFiles\Main\PS3_GAME\QuickBMS_STR_OUTPUT\"

# Get all subdirectories alphabetically
$subDirs = Get-ChildItem -Path $targetDir -Directory | Sort-Object Name

if (-not $subDirs) {
    Write-Host "No subdirectories found in $targetDir"
    exit
}

# First: list the contents of the target directory
Write-Host "`n==== Listing root: $targetDir ====" -ForegroundColor Cyan
Get-ChildItem -Path $targetDir

# Then: for each subdirectory, list its immediate contents (no recursion)
foreach ($dir in $subDirs) {
    Write-Host "`n---- Subdir: $($dir.FullName) ----" -ForegroundColor Yellow
    Get-ChildItem -Path $dir.FullName
}
