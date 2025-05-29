$basePath = "A:\Dev\Games\TheSimpsonsGame\PAL\reverse_engineering\Source\"  # Replace with your root directory path

# Get each format folder in the root
$formatFolders = Get-ChildItem -Path $basePath -Directory

#Write-Host "formatFolders: $formatFolders" -ForegroundColor Green
#Write-Host ""

foreach ($formatFolder in $formatFolders) {
	#Write-Host "Processing folder: $($formatFolder.FullName)" -ForegroundColor Green

    # Delete existing .hex files recursively in the current format folder
    $existingHexFiles = Get-ChildItem -Path $formatFolder.FullName -Filter *.hex -File -Recurse
    if ($existingHexFiles.Count -gt 0) {
        #Write-Host "Removing existing .hex files in $($formatFolder.FullName)..." -ForegroundColor Magenta
        $existingHexFiles | Remove-Item -Force
        #Write-Host ""
    }

    # Get all files recursively inside each format folder
	$files = Get-ChildItem -Path $formatFolder.FullName -Recurse -File | Where-Object { $_.Extension -notin @(".md", ".hex") }

	#Write-Host "files: $files" -ForegroundColor Green
	#Write-Host ""

	# Check if there are no files in the folder
	if ($files.Count -eq 0) {
		#Write-Host "No files found in $($formatFolder.FullName). Skipping..." -ForegroundColor Yellow
		#Write-Host ""
		continue
	}

	#Start-Sleep -Seconds 3

    foreach ($file in $files) {
		#Write-Host "Processing file: $($file.FullName)" -ForegroundColor Green
		#Start-Sleep -Seconds 5

        # Run Format-Hex on the file (limit to 65536 bytes)
        $hexOutput = Format-Hex -Path $file.FullName -Count 65536 | Out-String
		$hex24 = Format-Hex -Path $file.FullName -Count 24 | Out-String

		Write-Host "hex first 24: $($hex24)" -ForegroundColor Green

        # Output file name: place it next to the original file
        $outputPath = Join-Path -Path $file.DirectoryName -ChildPath ($file.Name + ".hex")

        # Write output to file
        $hexOutput | Out-File -FilePath $outputPath -Encoding utf8
    }
}
