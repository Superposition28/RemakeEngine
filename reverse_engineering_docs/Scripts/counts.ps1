# Define the target directory (replace with your actual path or pass as a parameter)
$targetDir = ".\GameFiles\Main\PS3_GAME"

# Define the log file path
$logFile = ".\Tools\test\counts.log"

# Function to write to the log file
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    Add-Content -Path $logFile -Value $Message
}

# Check if the target directory exists
if (-not (Test-Path -Path $targetDir -PathType Container)) {
    $errorMessage = "Error: Target directory '$targetDir' not found."
    Write-Host $errorMessage -ForegroundColor Red
    Write-Log $errorMessage
    exit # Or use 'return' if this is part of a larger script/function
}

# --- Level 1 ---
# List the immediate contents of the target directory (non-recursive)
$level1Header = "`n==== Listing root (Level 1): $targetDir ===="
Write-Host $level1Header -ForegroundColor Cyan
Write-Log $level1Header
$level1Contents = Get-ChildItem -Path $targetDir

foreach ($item in $level1Contents) {
    $level1Output = "`t[$($item.Name)]"
    Write-Host $level1Output
    Write-Log $level1Output

    if ($item.PSIsContainer) {
        # --- File Type Counting for this Level 1 subdirectory (Recursive) ---
        $filesInLevel1SubDirBranch = Get-ChildItem -Path $item.FullName -File -Recurse -ErrorAction SilentlyContinue
        $level1SubDirExtensionCounts = @{}
        foreach ($file in $filesInLevel1SubDirBranch) {
            if ([string]::IsNullOrWhiteSpace($file.Name)) { continue }
            $nameParts = $file.Name -split '\.'
            if ($nameParts.Length -lt 2) { continue }
            if ($file.Name.StartsWith('.') -and $nameParts.Length -eq 2) {
                $extensionChain = $nameParts[1].ToLower()
            } elseif ($nameParts[0] -eq '') {
                $extensions = $nameParts[1..($nameParts.Length - 1)]
                $extensionChain = ($extensions -join '.').ToLower()
            } else {
                $extensions = $nameParts[1..($nameParts.Length - 1)]
                $extensionChain = ($extensions -join '.').ToLower()
            }
            if ($level1SubDirExtensionCounts.ContainsKey($extensionChain)) {
                $level1SubDirExtensionCounts[$extensionChain]++
            } else {
                $level1SubDirExtensionCounts[$extensionChain] = 1
            }
        }

        if ($level1SubDirExtensionCounts.Count -gt 0) {
            $fileCountsHeader = "`t`tFile Type Counts in $($item.Name) (Recursive Downwards):"
            Write-Host $fileCountsHeader -ForegroundColor Green
            Write-Log $fileCountsHeader
            $level1SubDirExtensionCounts.GetEnumerator() |
                Sort-Object -Property Value -Descending |
                ForEach-Object {
                    $formattedOutput = "`t`t`t{0,-18} : {1}" -f $_.Name, $_.Value
                    Write-Host $formattedOutput
                    Write-Log $formattedOutput
                }
        }
    }
}

# --- File Type Counting for the entire root directory (Recursive) ---
$rootFilesRecursive = Get-ChildItem -Path $targetDir -File -Recurse -ErrorAction SilentlyContinue
$rootExtensionCounts = @{}
foreach ($file in $rootFilesRecursive) {
    if ([string]::IsNullOrWhiteSpace($file.Name)) { continue }
    $nameParts = $file.Name -split '\.'
    if ($nameParts.Length -lt 2) { continue }
    if ($file.Name.StartsWith('.') -and $nameParts.Length -eq 2) {
        $extensionChain = $nameParts[1].ToLower()
    } elseif ($nameParts[0] -eq '') {
        $extensions = $nameParts[1..($nameParts.Length - 1)]
        $extensionChain = ($extensions -join '.').ToLower()
    } else {
        $extensions = $nameParts[1..($nameParts.Length - 1)]
        $extensionChain = ($extensions -join '.').ToLower()
    }
    if ($rootExtensionCounts.ContainsKey($extensionChain)) {
        $rootExtensionCounts[$extensionChain]++
    } else {
        $rootExtensionCounts[$extensionChain] = 1
    }
}

if ($rootExtensionCounts.Count -gt 0) {
    $rootFileCountsHeader = "`nFile Type Counts in root (Recursive Downwards):"
    Write-Host $rootFileCountsHeader -ForegroundColor Green
    Write-Log $rootFileCountsHeader
    $rootExtensionCounts.GetEnumerator() |
        Sort-Object -Property Value -Descending |
        ForEach-Object {
            $formattedOutput = "`t{0,-18} : {1}" -f $_.Name, $_.Value
            Write-Host $formattedOutput
            Write-Log $formattedOutput
        }
}

# Get all immediate subdirectories of the root (Level 2 Dirs)
$level2Dirs = Get-ChildItem -Path $targetDir -Directory | Sort-Object Name

# Check if any Level 2 subdirectories were found
if (-not $level2Dirs) {
    $noSubdirsMessage = "`nNo subdirectories found in $targetDir"
    Write-Host $noSubdirsMessage -ForegroundColor Yellow
    Write-Log $noSubdirsMessage
} else {
    # --- Level 2 ---
    # Loop through each Level 2 directory
    foreach ($l2Dir in $level2Dirs) {
        $level2Header = "`n---- Subdir (Level 2): $($l2Dir.FullName) ----"
        Write-Host $level2Header -ForegroundColor Yellow
        Write-Log $level2Header

        # List its immediate contents (files and directories) (non-recursive)
        $level2ContentsHeader = "`n`tContents of $($l2Dir.Name):"
        Write-Host $level2ContentsHeader
        Write-Log $level2ContentsHeader
        $level2Contents = Get-ChildItem -Path $l2Dir.FullName

        foreach ($item in $level2Contents) {
            $level2Output = "`t  [$($item.Name)]"
            Write-Host $level2Output
            Write-Log $level2Output

            if ($item.PSIsContainer) {
                # --- File Type Counting for this Level 2 subdirectory (Recursive) ---
                $filesInLevel2SubDirBranch = Get-ChildItem -Path $item.FullName -File -Recurse -ErrorAction SilentlyContinue
                $level2SubDirExtensionCounts = @{}
                foreach ($file in $filesInLevel2SubDirBranch) {
                    if ([string]::IsNullOrWhiteSpace($file.Name)) { continue }
                    $nameParts = $file.Name -split '\.'
                    if ($nameParts.Length -lt 2) { continue }
                    if ($file.Name.StartsWith('.') -and $nameParts.Length -eq 2) {
                        $extensionChain = $nameParts[1].ToLower()
                    } elseif ($nameParts[0] -eq '') {
                        $extensions = $nameParts[1..($nameParts.Length - 1)]
                        $extensionChain = ($extensions -join '.').ToLower()
                    } else {
                        $extensions = $nameParts[1..($nameParts.Length - 1)]
                        $extensionChain = ($extensions -join '.').ToLower()
                    }
                    if ($level2SubDirExtensionCounts.ContainsKey($extensionChain)) {
                        $level2SubDirExtensionCounts[$extensionChain]++
                    } else {
                        $level2SubDirExtensionCounts[$extensionChain] = 1
                    }
                }

                if ($level2SubDirExtensionCounts.Count -gt 0) {
                    $fileCountsHeader = "`t  `tFile Type Counts in $($item.Name) (Recursive Downwards):"
                    Write-Host $fileCountsHeader -ForegroundColor Green
                    Write-Log $fileCountsHeader
                    $level2SubDirExtensionCounts.GetEnumerator() |
                        Sort-Object -Property Value -Descending |
                        ForEach-Object {
                            $formattedOutput = "`t  `t`t{0,-18} : {1}" -f $_.Name, $_.Value
                            Write-Host $formattedOutput
                            Write-Log $formattedOutput
                        }
                }
            }
        }
    } # End Level 2 loop
}

$scriptFinishedMessage = "`n==== Script Finished ===="
Write-Host $scriptFinishedMessage -ForegroundColor Magenta
Write-Log $scriptFinishedMessage

Write-Host "`nOutput logged to '$logFile'" -ForegroundColor Green