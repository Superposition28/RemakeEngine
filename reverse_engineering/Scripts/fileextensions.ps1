# Set the root directory
$root = "A:\Dev\Games\TheSimpsonsGame\Modules\Extract\GameFiles\quickbms_out"

# Get all files recursively
$allFiles = Get-ChildItem -Path $root -Recurse -File

# Create hashtable to store extension chains and their counts
$extensionCounts = @{}

# Go through each file
foreach ($file in $allFiles) {
    $nameParts = $file.Name -split '\.'

    # Skip files without any extension
    if ($nameParts.Length -lt 2) { continue }

    # Get all extensions (everything after the first part)
    $extensions = $nameParts[1..($nameParts.Length - 1)]
    $extensionChain = ($extensions -join '.').ToLower()

    # Count them
    if ($extensionCounts.ContainsKey($extensionChain)) {
        $extensionCounts[$extensionChain]++
    } else {
        $extensionCounts[$extensionChain] = 1
    }
}

# Sort and display the results
$extensionCounts.GetEnumerator() |
    Sort-Object -Property Value -Descending |
    Format-Table Name, Value -AutoSize
