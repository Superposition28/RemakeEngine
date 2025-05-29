# Set the root directory
$root = "GameFiles\Main\PS3_GAME\QuickBMS_STR_OUTPUT"

# Get all .ps3 files recursively
$ps3Files = Get-ChildItem -Path $root -Recurse -Filter *.ps3

# Create a hashtable to store counts
$subExtensionCounts = @{}

# Process each file
foreach ($file in $ps3Files) {
    $nameParts = $file.Name -split '\.'
    if ($nameParts.Length -ge 2) {
        $subExtWithPs3 = ($nameParts[$nameParts.Length - 2] + ".ps3").ToLower()
        if ($subExtensionCounts.ContainsKey($subExtWithPs3)) {
            $subExtensionCounts[$subExtWithPs3]++
        } else {
            $subExtensionCounts[$subExtWithPs3] = 1
        }
    }
}

# Sort and display the results
$subExtensionCounts.GetEnumerator() |
    Sort-Object -Property Value -Descending |
    Format-Table Name, Value -AutoSize


