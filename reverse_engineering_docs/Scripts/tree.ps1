function Show-Tree {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, Position=0)]
        [string]$Path,

        # Optional parameter to filter by file extension
        [Parameter(Mandatory=$false)]
        [string]$Extension,

        # Internal use parameters for recursion
        [string]$IndentPrefix = "",
        [switch]$IsRoot = $true
    )

    # --- Function Body ---
    $outputLines = [System.Collections.Generic.List[string]]::new()

    # Add the root path only on the initial call
    if ($IsRoot) {
        # Resolve the path to get the full absolute path
        $resolvedPath = Resolve-Path -Path $Path -ErrorAction SilentlyContinue
        if ($resolvedPath) {
            $outputLines.Add($resolvedPath.Path.ToUpper()) # Add the root path in uppercase
        } else {
            $outputLines.Add("Error: Path not found or inaccessible: $Path")
            return $outputLines
        }
    }

    # Get child items (files and directories), handle potential errors
    # Sort directories first, then files, then by name for consistent ordering
    $items = Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Sort-Object -Property @{Expression={$_.PSIsContainer}; Descending=$false}, Name

    if ($null -eq $items) {
        # Path might be inaccessible or empty, just return what we have
        return $outputLines
    }

    $lastItemIndex = $items.Count - 1

    # Iterate through each item (file or directory) at the current level
    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $isLast = ($i -eq $lastItemIndex)

        # Determine branch connector for directories
        $itemConnector = if ($isLast) { '\---' } else { '+---' }

        # Determine prefix continuation for children IF the PARENT ($item) is a directory
        $recursiveChildPrefixContinuation = if ($isLast) { '    ' } else { '|   ' }
        $recursiveChildPrefix = $IndentPrefix + $recursiveChildPrefixContinuation

        if ($item.PSIsContainer) {
            # Print directory line
            $outputLines.Add($IndentPrefix + $itemConnector + $item.Name)
            # Recurse using the standard child prefix, passing the extension filter
            $childLinesResult = @(Show-Tree -Path $item.FullName -IndentPrefix $recursiveChildPrefix -Extension $Extension -IsRoot:$false)
            if ($null -ne $childLinesResult -and $childLinesResult.Count -gt 0) {
                $outputLines.AddRange([string[]]$childLinesResult)
            }
        } else {
            # It's a file. Check if we need to filter by extension.
            $shouldAddFile = $true # Assume we add the file by default
            if (-not [string]::IsNullOrEmpty($Extension)) {
                # Ensure the provided extension starts with a dot for comparison
                $filterExt = if ($Extension.StartsWith('.')) { $Extension } else { ".$Extension" }
                if ($item.Extension -ne $filterExt) {
                    $shouldAddFile = $false # Don't add if extension doesn't match
                }
            }

            if ($shouldAddFile) {
                # Construct the specific prefix for file lines using spaces '    ' for the last segment.
                $fileLinePrefix = $IndentPrefix + '    '
                $outputLines.Add($fileLinePrefix + $item.Name)
            }
        }
    }

    # Return the collected lines for this level and below
    return $outputLines
}

# --- How to Use ---

# Check for help request first
if ($args -contains '-help' -or $args -contains '/h' -or $args -contains '/?') {
    Write-Host @"
Usage: .\tree.ps1 [Path] [Extension]

Arguments:
  Path       (Optional) The directory path to display the tree for.
             Defaults to the current directory if omitted.
  Extension  (Optional) Filter the output to only show files with this extension.
             Include the leading dot (e.g., .txt) or omit it (e.g., txt).

Examples:
  .\tree.ps1                  # Show tree for current directory
  .\tree.ps1 C:\Users         # Show tree for C:\Users
  .\tree.ps1 C:\Windows .log  # Show tree for C:\Windows, only .log files
  .\tree.ps1 . ps1            # Show tree for current directory, only .ps1 files
  .\tree.ps1 -help            # Display this help message
"@
    exit # Exit after showing help
}

# Get the path from the command line arguments, or use current directory if none provided
# Simple argument parsing: assumes first arg is path, second (if present) is extension
$rootPath = $null
$fileExtension = $null

if ($args.Count -ge 1) {
    $rootPath = $args[0]
} else {
    $rootPath = (Get-Location).Path # Use current location
}
if ($args.Count -ge 2) {
    $fileExtension = $args[1]
}

# Execute the function and capture the output
# Pass the extension if provided
$treeOutput = if ($fileExtension) {
    Show-Tree -Path $rootPath -Extension $fileExtension
} else {
    Show-Tree -Path $rootPath
}

# Display output to console
if ($treeOutput) {
    $treeOutput
} else {
    Write-Warning "Failed to generate tree structure for path: $rootPath"
}