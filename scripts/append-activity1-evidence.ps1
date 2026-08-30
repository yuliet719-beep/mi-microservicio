$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$reportPath = Join-Path $repositoryRoot 'docs\Actividad_1_Laboratorio_Tecnico.docx'
$evidence = @(
    @{ Caption = 'Figura 1. Ejecucion exitosa de GitHub Actions con Snyk y SonarCloud.'; File = 'docs\evidencia-github-actions-snyk-sonarcloud.png' },
    @{ Caption = 'Figura 2. Quality Gate aprobado en SonarQube Cloud.'; File = 'docs\evidencia-sonarcloud-quality-gate.png' },
    @{ Caption = 'Figura 3. Target del microservicio en estado UP en Prometheus.'; File = 'docs\evidencia-prometheus-target.png' },
    @{ Caption = 'Figura 4. Dashboard Grafana con metricas operativas.'; File = 'docs\evidencia-grafana-dashboard.png' },
    @{ Caption = 'Figura 5. Pipeline Overview autenticado de Jenkins, build #7 exitoso.'; File = 'docs\evidencia-jenkins-build-7.png' }
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$wdCollapseEnd = 0
$wdPageBreak = 7

try {
    $document = $word.Documents.Open($reportPath)
    $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $range.InsertBreak($wdPageBreak)
    $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $range.Text = 'Anexo A. Evidencias fotograficas de la ejecucion'
    $range.Font.Bold = 1
    $range.Font.Size = 14
    $range.InsertParagraphAfter() | Out-Null

    foreach ($item in $evidence) {
        $imagePath = Join-Path $repositoryRoot $item.File
        if (Test-Path $imagePath) {
            $captionRange = $document.Range($document.Content.End - 1, $document.Content.End - 1)
            $captionRange.Text = $item.Caption
            $captionRange.Font.Italic = 1
            $captionRange.Font.Size = 10
            $captionRange.InsertParagraphAfter() | Out-Null

            $imageRange = $document.Range($document.Content.End - 1, $document.Content.End - 1)
            $imageRange.Collapse($wdCollapseEnd)
            $image = $document.InlineShapes.AddPicture($imagePath, $false, $true, $imageRange)
            $image.Width = 460
            if ($image.Height -gt 320) { $image.Height = 320 }

            $afterImage = $document.Range($document.Content.End - 1, $document.Content.End - 1)
            $afterImage.InsertParagraphAfter() | Out-Null
        }
    }

    $document.Save()
    $document.Close()
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}