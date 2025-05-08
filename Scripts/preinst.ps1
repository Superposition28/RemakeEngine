# Set the root directory
$root = "GameFiles\Main\PS3_GAME\QuickBMS_STR_OUTPUT"

# Get all .preinstanced files recursively
$preinstancedFiles = Get-ChildItem -Path $root -Recurse -Filter *.preinstanced

# Create a hashtable to store counts
$subExtensionCounts = @{}

# Process each file
foreach ($file in $preinstancedFiles) {
    $nameParts = $file.Name -split '\.'
    
    if ($nameParts.Length -ge 3) {
        # Combine the last two sub-extensions with .preinstanced (e.g., sub1.sub2.preinstanced)
        $subExtCombo = ($nameParts[$nameParts.Length - 3] + "." + $nameParts[$nameParts.Length - 2] + ".preinstanced").ToLower()
        
        if ($subExtensionCounts.ContainsKey($subExtCombo)) {
            $subExtensionCounts[$subExtCombo]++
        } else {
            $subExtensionCounts[$subExtCombo] = 1
        }
    } elseif ($nameParts.Length -ge 2) {
        # Fallback: only one sub-extension before .preinstanced
        $subExtCombo = ($nameParts[$nameParts.Length - 2] + ".preinstanced").ToLower()
        
        if ($subExtensionCounts.ContainsKey($subExtCombo)) {
            $subExtensionCounts[$subExtCombo]++
        } else {
            $subExtensionCounts[$subExtCombo] = 1
        }
    }
}

# Sort and display the results
$subExtensionCounts.GetEnumerator() |
    Sort-Object -Property Value -Descending |
    Format-Table Name, Value -AutoSize
