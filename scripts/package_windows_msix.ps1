param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDirectory,
    [Parameter(Mandatory = $true)]
    [string]$ArtifactName,
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [Parameter(Mandatory = $true)]
    [string]$CertificateThumbprint,
    [string]$PublisherDisplayName = "SB Automation Suite",
    [string]$TimestampUrl = "",
    [string]$OutputDirectory = "",
    [switch]$Overwrite
)

$ErrorActionPreference = "Stop"
$minimumSdkVersion = [version]"10.0.22000.0"
$projectRoot = Split-Path -Parent $PSScriptRoot
$manifestTemplate = Join-Path $projectRoot `
    "packaging\windows\AppxManifest.xml.in"
$logoSource = Join-Path $projectRoot "data\logo\Logo_cami.png"

function Find-WindowsSdkTool {
    param([Parameter(Mandatory = $true)][string]$Name)

    $sdkBin = Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\bin"
    if (-not (Test-Path -LiteralPath $sdkBin)) {
        throw "Windows SDK no está instalado."
    }

    foreach ($directory in (
        Get-ChildItem -LiteralPath $sdkBin -Directory |
            Where-Object { $_.Name -match '^\d+(\.\d+){3}$' } |
            Sort-Object { [version]$_.Name } -Descending
    )) {
        if ([version]$directory.Name -lt $minimumSdkVersion) {
            continue
        }
        $candidate = Join-Path $directory.FullName "x64\$Name"
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    throw "Se necesita Windows 11 SDK 10.0.22000 o posterior."
}

function ConvertTo-PackageVersion {
    param([Parameter(Mandatory = $true)][string]$Value)

    if ($Value -notmatch '^\d+\.\d+(\.\d+)?(\.\d+)?$') {
        throw "La versión MSIX debe ser numérica."
    }
    $parts = [System.Collections.Generic.List[int]]::new()
    foreach ($part in $Value.Split('.')) {
        $number = [int]$part
        if ($number -gt 65535) {
            throw "Cada parte de la versión MSIX debe ser menor que 65536."
        }
        $parts.Add($number)
    }
    while ($parts.Count -lt 4) {
        $parts.Add(0)
    }
    return ($parts -join '.')
}

function New-SquareLogo {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][int]$Size
    )

    Add-Type -AssemblyName System.Drawing
    $image = [System.Drawing.Image]::FromFile($Source)
    $bitmap = $null
    $graphics = $null
    try {
        $bitmap = [System.Drawing.Bitmap]::new(
            $Size,
            $Size,
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.Clear([System.Drawing.Color]::Transparent)
        $graphics.InterpolationMode = `
            [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.PixelOffsetMode = `
            [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $available = [Math]::Max(1, [Math]::Floor($Size * 0.88))
        $scale = [Math]::Min(
            $available / $image.Width,
            $available / $image.Height
        )
        $width = [Math]::Max(1, [Math]::Round($image.Width * $scale))
        $height = [Math]::Max(1, [Math]::Round($image.Height * $scale))
        $left = [Math]::Floor(($Size - $width) / 2)
        $top = [Math]::Floor(($Size - $height) / 2)
        $rectangle = [System.Drawing.Rectangle]::new(
            $left,
            $top,
            $width,
            $height
        )
        $graphics.DrawImage($image, $rectangle)
        $bitmap.Save(
            $Destination,
            [System.Drawing.Imaging.ImageFormat]::Png
        )
    }
    finally {
        if ($graphics) {
            $graphics.Dispose()
        }
        if ($bitmap) {
            $bitmap.Dispose()
        }
        $image.Dispose()
    }
}

if ($ArtifactName -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') {
    throw "El nombre del artefacto contiene caracteres no válidos."
}
$packageVersion = ConvertTo-PackageVersion $Version
$source = (Resolve-Path -LiteralPath $SourceDirectory).Path
$executableName = "$ArtifactName.exe"
if (-not (Test-Path -LiteralPath (Join-Path $source $executableName))) {
    throw "No se encontró $executableName en la distribución."
}
foreach ($requiredPath in @($manifestTemplate, $logoSource)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Falta un recurso de empaquetado: $requiredPath"
    }
}

$thumbprint = ($CertificateThumbprint -replace '\s', '').ToUpperInvariant()
if ($thumbprint -notmatch '^[A-F0-9]{40}$') {
    throw "El thumbprint del certificado no es válido."
}
$certificate = Get-Item -LiteralPath "Cert:\CurrentUser\My\$thumbprint" `
    -ErrorAction Stop
if (-not $certificate.HasPrivateKey) {
    throw "El certificado no contiene una clave privada."
}
if ($certificate.NotAfter -le (Get-Date)) {
    throw "El certificado de firma está caducado."
}
$codeSigningOid = "1.3.6.1.5.5.7.3.3"
$enhancedKeyUsages = @(
    $certificate.EnhancedKeyUsageList |
        ForEach-Object { [string]$_.ObjectId }
)
if (
    $enhancedKeyUsages.Count -gt 0 -and
    $enhancedKeyUsages -notcontains $codeSigningOid
) {
    throw "El certificado no permite firma de código."
}

$makeAppx = Find-WindowsSdkTool "makeappx.exe"
$signTool = Find-WindowsSdkTool "signtool.exe"
$outputRoot = if ($OutputDirectory) {
    [System.IO.Path]::GetFullPath($OutputDirectory)
} else {
    Join-Path $projectRoot "release"
}
$packagePath = Join-Path $outputRoot "${ArtifactName}_x64.msix"
if ((Test-Path -LiteralPath $packagePath) -and -not $Overwrite) {
    throw "El paquete ya existe. Usa -Overwrite para sustituirlo."
}

$stagingRoot = Join-Path $projectRoot `
    ("build\msix-" + [Guid]::NewGuid().ToString("N"))
$layout = Join-Path $stagingRoot "layout"
$unpacked = Join-Path $stagingRoot "unpacked"
$stagedPackage = Join-Path $stagingRoot "${ArtifactName}_x64.msix"
try {
    New-Item -ItemType Directory -Path $layout -Force | Out-Null
    Get-ChildItem -LiteralPath $source -Force | Copy-Item `
        -Destination $layout -Recurse -Force

    $assets = Join-Path $layout "Assets"
    New-Item -ItemType Directory -Path $assets -Force | Out-Null
    New-SquareLogo $logoSource (Join-Path $assets "StoreLogo.png") 50
    New-SquareLogo `
        $logoSource `
        (Join-Path $assets "Square44x44Logo.png") `
        44
    New-SquareLogo `
        $logoSource `
        (Join-Path $assets "Square150x150Logo.png") `
        150

    $publisher = [System.Security.SecurityElement]::Escape(
        $certificate.Subject
    )
    $displayName = [System.Security.SecurityElement]::Escape(
        $PublisherDisplayName
    )
    $manifest = (Get-Content -LiteralPath $manifestTemplate -Raw).
        Replace("{{PUBLISHER}}", $publisher).
        Replace("{{PUBLISHER_DISPLAY_NAME}}", $displayName).
        Replace("{{VERSION}}", $packageVersion).
        Replace("{{EXECUTABLE}}", $executableName)
    $manifestPath = Join-Path $layout "AppxManifest.xml"
    Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding utf8

    $packArguments = @(
        "pack",
        "/v",
        "/h", "SHA256",
        "/d", $layout,
        "/p", $stagedPackage,
        "/no"
    )
    & $makeAppx @packArguments
    if ($LASTEXITCODE -ne 0) {
        throw "MakeAppx no pudo crear el paquete."
    }

    $signArguments = @(
        "sign",
        "/fd", "SHA256",
        "/sha1", $thumbprint,
        "/s", "My"
    )
    if ($TimestampUrl) {
        $signArguments += @("/tr", $TimestampUrl, "/td", "SHA256")
    }
    $signArguments += $stagedPackage
    & $signTool @signArguments
    if ($LASTEXITCODE -ne 0) {
        throw "SignTool no pudo firmar el paquete."
    }
    & $signTool verify /pa /all /v $stagedPackage
    if ($LASTEXITCODE -ne 0) {
        throw "La firma del paquete no es válida o no es de confianza."
    }

    & $makeAppx unpack /p $stagedPackage /d $unpacked
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo validar la extracción del paquete."
    }
    $unpackedManifest = Get-Content `
        -LiteralPath (Join-Path $unpacked "AppxManifest.xml") `
        -Raw
    foreach ($capability in @(
        "graphicsCaptureProgrammatic",
        "graphicsCaptureWithoutBorder",
        "runFullTrust"
    )) {
        if ($unpackedManifest -notmatch [regex]::Escape($capability)) {
            throw "Falta la capacidad MSIX $capability."
        }
    }
    if (-not (Test-Path -LiteralPath (
        Join-Path $unpacked $executableName
    ))) {
        throw "El ejecutable no está presente en el paquete MSIX."
    }

    $hash = Get-FileHash -LiteralPath $stagedPackage -Algorithm SHA256
    New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
    if (Test-Path -LiteralPath $packagePath) {
        if (-not $Overwrite) {
            throw "El paquete ya existe. Usa -Overwrite para sustituirlo."
        }
        Move-Item -LiteralPath $stagedPackage -Destination $packagePath -Force
    } else {
        Move-Item -LiteralPath $stagedPackage -Destination $packagePath
    }
    Write-Output "MSIX_OK"
    Write-Output "Package: $packagePath"
    Write-Output "SHA256: $($hash.Hash)"
}
finally {
    if (Test-Path -LiteralPath $stagingRoot) {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force
    }
}
