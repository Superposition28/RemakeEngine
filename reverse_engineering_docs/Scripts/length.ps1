# Set the root directory to search
$rootPath = "A:\Dev\Games\TheSimpsonsGame\GameFiles\Main\PS3_GAME\Flattened_OUTPUT"

# Number of path segments to keep at the end
$keepSegments = 9 # adjust as needed (e.g., 3 folders + filename)

# Store matched results
$results = @()

# Process .txd files
Get-ChildItem -Path $rootPath -Recurse -Filter *.txd -File | ForEach-Object {
    $fullPath = $_.FullName
    $length = $fullPath.Length

    if ($length -gt 200) {
        $segments = $fullPath -split '\\'
        $shortPath = ($segments[-$keepSegments..-1] -join '\')
        $results += [PSCustomObject]@{
            Length    = $length
            ShortPath = "...\$shortPath"
        }
    }
}

# Output results
$results | Format-Table -AutoSize

# Output the longest path length
if ($results.Count -gt 0) {
    $maxLength = ($results | Measure-Object -Property Length -Maximum).Maximum
    Write-Host "`nLongest path length: $maxLength" -ForegroundColor Cyan

    # Output the total count of files exceeding the length limit
    $totalExceeding = $results.Count
    Write-Host "Total files exceeding length limit: $totalExceeding" -ForegroundColor Green
} else {
    Write-Host "No .txd files with path length over 255 characters found." -ForegroundColor Yellow
}