# Set the root directory to scan
$rootPath = "GameFiles\Main\PS3_GAME\USRDIR"  # Change this to your root directory
$minCount = 2                      # Only show folder names that appear more than this number

# Get all directories recursively
$allDirs = Get-ChildItem -Path $rootPath -Directory -Recurse

# Group by folder name and filter by count
$folderNameCounts = $allDirs |
    Group-Object -Property Name |
    Where-Object { $_.Count -gt $minCount } |
    Sort-Object -Property Count -Descending

# Print the results
foreach ($group in $folderNameCounts) {
    "{0,-30} {1,5}" -f $group.Name, $group.Count
}
