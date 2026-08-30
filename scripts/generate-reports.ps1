$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$wdFormatDocumentDefault = 16
$wdStyleTitle = -63
$wdStyleHeading1 = -2
$wdStyleHeading2 = -3

$reports = @(
    @{
        Source = Join-Path $repositoryRoot 'docs\ACTIVIDAD_1_INFORME.md'
        Output = Join-Path $repositoryRoot 'docs\Actividad_1_Laboratorio_Tecnico.docx'
    },
    @{
        Source = Join-Path $repositoryRoot 'docs\ACTIVIDAD_2_INFORME.md'
        Output = Join-Path $repositoryRoot 'docs\Actividad_2_Estudio_de_Caso.docx'
    }
)

try {
    foreach ($report in $reports) {
        $document = $word.Documents.Add()
        $inCodeBlock = $false

        foreach ($line in Get-Content $report.Source) {
            if ($line -eq '```' -or $line -like '```*') {
                $inCodeBlock = -not $inCodeBlock
                continue
            }

            $paragraph = $document.Content.Paragraphs.Add()
            $paragraph.Range.Text = $line

            if ($line -match '^# (.+)') {
                $paragraph.Range.Text = $matches[1]
                $paragraph.Range.Style = $wdStyleTitle
            }
            elseif ($line -match '^## (.+)') {
                $paragraph.Range.Text = $matches[1]
                $paragraph.Range.Style = $wdStyleHeading1
            }
            elseif ($line -match '^### (.+)') {
                $paragraph.Range.Text = $matches[1]
                $paragraph.Range.Style = $wdStyleHeading2
            }
            elseif ($line -match '^\d+\. (.+)') {
                $paragraph.Range.Text = $matches[1]
                $paragraph.Range.ListFormat.ApplyNumberDefault()
            }
            elseif ($line -match '^- (.+)') {
                $paragraph.Range.Text = $matches[1]
                $paragraph.Range.ListFormat.ApplyBulletDefault()
            }
            elseif ($inCodeBlock) {
                $paragraph.Range.Font.Name = 'Consolas'
                $paragraph.Range.Font.Size = 9
            }
            else {
                $paragraph.Range.Font.Name = 'Aptos'
                $paragraph.Range.Font.Size = 11
            }

            $paragraph.Range.InsertParagraphAfter() | Out-Null
        }

        if ($report.Output -like '*Actividad_2_*') {
            $visualHeading = $document.Content.Paragraphs.Add()
            $visualHeading.Range.Text = 'Representacion visual: DevOps -> MLOps'
            $visualHeading.Range.Style = $wdStyleHeading1
            $visualHeading.Range.InsertParagraphAfter() | Out-Null

            $tableRange = $document.Bookmarks.Item('\endofdoc').Range
            $table = $document.Tables.Add($tableRange, 5, 3)
            $table.Cell(1, 1).Range.Text = 'Dimension'
            $table.Cell(1, 2).Range.Text = 'DevOps'
            $table.Cell(1, 3).Range.Text = 'MLOps'
            $table.Cell(2, 1).Range.Text = 'Entrada'
            $table.Cell(2, 2).Range.Text = 'Codigo y configuracion'
            $table.Cell(2, 3).Range.Text = 'Codigo, datos y caracteristicas'
            $table.Cell(3, 1).Range.Text = 'Artefacto'
            $table.Cell(3, 2).Range.Text = 'Imagen o binario'
            $table.Cell(3, 3).Range.Text = 'Imagen, modelo y metadatos'
            $table.Cell(4, 1).Range.Text = 'Validacion'
            $table.Cell(4, 2).Range.Text = 'Pruebas, calidad y seguridad'
            $table.Cell(4, 3).Range.Text = 'Pruebas mas calidad de datos y modelo'
            $table.Cell(5, 1).Range.Text = 'Operacion'
            $table.Cell(5, 2).Range.Text = 'Disponibilidad, latencia y errores'
            $table.Cell(5, 3).Range.Text = 'Operacion mas drift, sesgo y precision'
            $table.Rows.Item(1).Range.Bold = 1
            $table.Rows.Item(1).Shading.BackgroundPatternColor = 14277081
            $table.Borders.Enable = 1
        }

        if ($report.Output -like '*Actividad_1_*') {
            $evidenceImage = Join-Path $repositoryRoot 'docs\evidencia-grafana-dashboard.png'
            if (Test-Path $evidenceImage) {
                $evidenceHeading = $document.Content.Paragraphs.Add()
                $evidenceHeading.Range.Text = 'Evidencia visual: dashboard Grafana activo'
                $evidenceHeading.Range.Style = $wdStyleHeading1
                $evidenceHeading.Range.InsertParagraphAfter() | Out-Null

                $imageRange = $document.Bookmarks.Item('\endofdoc').Range
                $image = $document.InlineShapes.AddPicture($evidenceImage, $false, $true, $imageRange)
                $image.Width = 460
                $image.Height = 260
            }
        }

        $document.SaveAs([ref]$report.Output, [ref]$wdFormatDocumentDefault)
        $document.Close()
    }
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}