# Porta seriale ESP32
$port = "COM7"


# esptool --port COM7 erase_flash

# esptool --port COM7 --baud 460800 write_flash 0x1000 ESP32_GENERIC-20250911-v1.26.1.bin
# -------------------------------------------------------------------
# 1. Rileva le cartelle del progetto
# -------------------------------------------------------------------
$folders = Get-ChildItem -Directory | Where-Object {
    $_.Name -notin @(".vscode", ".git")
} | Select-Object -ExpandProperty Name

# -------------------------------------------------------------------
# 2. Crea create_folders.py in locale
# -------------------------------------------------------------------
# Prepara la lista di cartelle in formato Python ["moduli","utils","config"]
$foldersQuoted = $folders | ForEach-Object { '"' + $_ + '"' }
$foldersList = $foldersQuoted -join ","

$createFoldersCode = @"
#!/usr/bin/env python3
import os

folders = [$foldersList]

for folder in folders:
    try:
        if folder not in os.listdir():
            os.mkdir(folder)
            print(f"Created folder: {folder}")
        else:
            print(f"Folder already exists: {folder}")
    except Exception as e:
        print(f"Error creating folder {folder}: {e}")
"@

$createFoldersCode | Out-File -FilePath "create_folders.py" -Encoding ascii

# -------------------------------------------------------------------
# 3. Copia create_folders.py sulla ESP32
# -------------------------------------------------------------------
ampy --port $port put create_folders.py

# -------------------------------------------------------------------
# 4. Esegui create_folders.py direttamente sulla ESP32
# -------------------------------------------------------------------
ampy --port $port run create_folders.py

# -------------------------------------------------------------------
# 5. Cancella create_folders.py dalla ESP32
# -------------------------------------------------------------------
ampy --port $port rm create_folders.py

# -------------------------------------------------------------------
# 6. Carica tutti i file del progetto
# -------------------------------------------------------------------
$files = Get-ChildItem -Recurse -File | Where-Object {
    $_.FullName -notmatch "\\.vscode" -and
    $_.Extension -notin @(".ps1", ".fzz", ".bin") -and
    $_.Name -ne "create_folders.py"
}

foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($PSScriptRoot.Length + 1).Replace("\", "/")
    Write-Host "Uploading $relativePath..."
    ampy --port $port put $file.FullName $relativePath
}

# -------------------------------------------------------------------
# 7. Rimuovi il file temporaneo locale
# -------------------------------------------------------------------
Remove-Item create_folders.py

# python -m serial.tools.miniterm COM7 115200 --exit-char 3 
