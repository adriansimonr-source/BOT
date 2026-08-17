param(
    [switch]$SkipTests,
    [string]$Version = "1.1.1"
)

$ErrorActionPreference = "Stop"
if ($Version -notmatch '^\d+\.\d+(\.\d+)?$') {
    throw "La versión debe tener formato numérico, por ejemplo 1.1 o 1.1.0."
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$buildPython = Join-Path $projectRoot ".build-venv\Scripts\python.exe"
$requirements = Join-Path $projectRoot "requirements.txt"
$buildRequirements = Join-Path $projectRoot "requirements-build.txt"
$spec = Join-Path $projectRoot "SB_Automation_Suite.spec"
$distDirectory = Join-Path $projectRoot "dist\SB_Automation_Suite"
$executable = Join-Path $distDirectory "SB_Automation_Suite.exe"
$pythonDll = Join-Path $distDirectory "_internal\python314.dll"
$packageReadme = Join-Path $distDirectory "LEEME_PRIMERO.txt"
$releaseDirectory = Join-Path $projectRoot "release"
$archive = Join-Path $releaseDirectory `
    "SB_Automation_Suite_v${Version}_Windows_x64.zip"

Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath $buildPython)) {
        & py -3.14 -m venv (Join-Path $projectRoot ".build-venv")
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo crear el entorno de build."
        }
    }

    & $buildPython -m pip install --disable-pip-version-check `
        -r $requirements -r $buildRequirements
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron instalar las dependencias de build."
    }

    & $buildPython -m pip check
    if ($LASTEXITCODE -ne 0) {
        throw "El entorno de build contiene dependencias incompatibles."
    }

    if (-not $SkipTests) {
        $previousQtPlatform = $env:QT_QPA_PLATFORM
        $env:QT_QPA_PLATFORM = "offscreen"
        try {
            & $buildPython -m unittest discover -s tests -p "test_*.py" -q
            if ($LASTEXITCODE -ne 0) {
                throw "La suite automatizada ha fallado."
            }
        }
        finally {
            $env:QT_QPA_PLATFORM = $previousQtPlatform
        }
    }

    $tesseractCommand = Get-Command tesseract -ErrorAction Stop
    $env:TESSERACT_HOME = Split-Path -Parent $tesseractCommand.Source

    & $buildPython -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath (Join-Path $projectRoot "dist") `
        --workpath (Join-Path $projectRoot "build") `
        $spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller no pudo generar la distribución."
    }

    @(
        "SB Automation Suite v$Version",
        "",
        "1. Extrae la carpeta SB_Automation_Suite completa del ZIP.",
        "2. Ejecuta SB_Automation_Suite.exe desde esa carpeta.",
        "3. No lo abras dentro del ZIP ni separes el EXE de _internal.",
        "",
        "La aplicacion incluye Python, Tesseract y sus dependencias."
    ) | Set-Content -LiteralPath $packageReadme -Encoding utf8

    $requiredFiles = @(
        $executable,
        $pythonDll,
        $packageReadme,
        (Join-Path $distDirectory "_internal\data\templates.json"),
        (Join-Path $distDirectory "_internal\data\templates\anchors\player_anchor.png"),
        (Join-Path $distDirectory "_internal\data\templates\anchors\enemy_anchor.png"),
        (Join-Path $distDirectory "_internal\data\templates\anchors\minimap_anchor.png"),
        (Join-Path $distDirectory "_internal\tesseract\tesseract.exe"),
        (Join-Path $distDirectory "_internal\tesseract\tessdata\eng.traineddata")
    )
    foreach ($path in $requiredFiles) {
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Falta un recurso en la build: $path"
        }
    }

    $smokeData = Join-Path $projectRoot `
        ("build\smoke-data-" + [Guid]::NewGuid().ToString("N"))
    $previousDataDirectory = $env:SB_AUTOMATION_DATA_DIR
    $previousQtPlatform = $env:QT_QPA_PLATFORM
    $env:SB_AUTOMATION_DATA_DIR = $smokeData
    $env:QT_QPA_PLATFORM = "offscreen"
    try {
        $smokeProcess = Start-Process `
            -FilePath $executable `
            -ArgumentList "--smoke-test" `
            -WorkingDirectory $distDirectory `
            -WindowStyle Hidden `
            -Wait `
            -PassThru
        if ($smokeProcess.ExitCode -ne 0) {
            throw "El ejecutable no superó el smoke test."
        }
    }
    finally {
        $env:SB_AUTOMATION_DATA_DIR = $previousDataDirectory
        $env:QT_QPA_PLATFORM = $previousQtPlatform
    }

    & (Join-Path $distDirectory "_internal\tesseract\tesseract.exe") `
        --version | Select-Object -First 1
    if ($LASTEXITCODE -ne 0) {
        throw "El Tesseract incluido no se puede ejecutar."
    }

    New-Item -ItemType Directory -Path $releaseDirectory -Force | Out-Null
    if (Test-Path -LiteralPath $archive) {
        Remove-Item -LiteralPath $archive -Force
    }
    Compress-Archive -LiteralPath $distDirectory -DestinationPath $archive

    $archiveSmokeRoot = Join-Path $projectRoot `
        ("build\archive-smoke-" + [Guid]::NewGuid().ToString("N"))
    $archiveSmokeData = Join-Path $projectRoot `
        ("build\archive-smoke-data-" + [Guid]::NewGuid().ToString("N"))
    try {
        Expand-Archive -LiteralPath $archive -DestinationPath $archiveSmokeRoot
        $archiveApp = Join-Path $archiveSmokeRoot "SB_Automation_Suite"
        $archiveExecutable = Join-Path $archiveApp "SB_Automation_Suite.exe"
        $archivePythonDll = Join-Path $archiveApp "_internal\python314.dll"
        $archiveReadme = Join-Path $archiveApp "LEEME_PRIMERO.txt"
        foreach ($path in @(
            $archiveExecutable,
            $archivePythonDll,
            $archiveReadme
        )) {
            if (-not (Test-Path -LiteralPath $path)) {
                throw "Falta un archivo tras extraer el ZIP: $path"
            }
        }

        $previousDataDirectory = $env:SB_AUTOMATION_DATA_DIR
        $previousQtPlatform = $env:QT_QPA_PLATFORM
        $env:SB_AUTOMATION_DATA_DIR = $archiveSmokeData
        $env:QT_QPA_PLATFORM = "offscreen"
        try {
            $archiveSmokeProcess = Start-Process `
                -FilePath $archiveExecutable `
                -ArgumentList "--smoke-test" `
                -WorkingDirectory $archiveApp `
                -WindowStyle Hidden `
                -Wait `
                -PassThru
            if ($archiveSmokeProcess.ExitCode -ne 0) {
                throw "El ejecutable extraído del ZIP no superó el smoke test."
            }
        }
        finally {
            $env:SB_AUTOMATION_DATA_DIR = $previousDataDirectory
            $env:QT_QPA_PLATFORM = $previousQtPlatform
        }
    }
    finally {
        if (Test-Path -LiteralPath $archiveSmokeRoot) {
            Remove-Item -LiteralPath $archiveSmokeRoot -Recurse -Force
        }
        if (Test-Path -LiteralPath $archiveSmokeData) {
            Remove-Item -LiteralPath $archiveSmokeData -Recurse -Force
        }
    }

    $hash = Get-FileHash -LiteralPath $archive -Algorithm SHA256
    $sizeMiB = [Math]::Round((Get-Item -LiteralPath $archive).Length / 1MB, 2)
    Write-Output "BUILD_OK"
    Write-Output "Executable: $executable"
    Write-Output "Archive: $archive"
    Write-Output "Archive size: $sizeMiB MiB"
    Write-Output "SHA256: $($hash.Hash)"
}
finally {
    Pop-Location
}
