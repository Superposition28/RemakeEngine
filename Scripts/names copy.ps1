# Set the root directory to scan
$rootPath = "GameFiles\Main\PS3_GAME\Flattened_OUTPUT"  # Change this to your root directory
$minCount = 4                                              # Only show folder names that appear more than this number

# Get all directories recursively
$allDirs = Get-ChildItem -Path $rootPath -Directory -Recurse

# Normalize folder names by replacing numbers with a placeholder (e.g., "#")
$normalizedNames = $allDirs | ForEach-Object {
    $normalized = $_.Name -replace '\d+', '#'
    [PSCustomObject]@{
        Original = $_.Name
        Normalized = $normalized
    }
}

# Group by normalized name, count, and filter
$grouped = $normalizedNames |
    Group-Object -Property Normalized |
    Where-Object { $_.Count -gt $minCount } |
    Sort-Object -Property Count -Descending

# Print results
foreach ($group in $grouped) {
    "{0,-30} {1,5}" -f $group.Name, $group.Count
}
