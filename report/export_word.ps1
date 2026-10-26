param(
    [string]$DocumentPath = (Join-Path $PSScriptRoot '..\output\report\HashLab_Project_Report.docx'),
    [string]$PdfPath = (Join-Path $PSScriptRoot '..\output\report\HashLab_Project_Report.pdf')
)
$ErrorActionPreference = 'Stop'
$resolvedDocument = [System.IO.Path]::GetFullPath($DocumentPath)
$resolvedPdf = [System.IO.Path]::GetFullPath($PdfPath)
$wordApp = $null
$reportDocument = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $reportDocument = $wordApp.Documents.Open($resolvedDocument, $false, $false)
    $reportDocument.Repaginate()
    foreach ($contentsTable in $reportDocument.TablesOfContents) { $contentsTable.Update() }
    $reportDocument.Fields.Update() | Out-Null
    $reportDocument.Repaginate()
    foreach ($contentsTable in $reportDocument.TablesOfContents) { $contentsTable.UpdatePageNumbers() }
    $reportDocument.Save()
    $reportDocument.ExportAsFixedFormat($resolvedPdf, 17)
    Write-Output "Exported report to $resolvedPdf"
    Write-Output "Pages: $($reportDocument.ComputeStatistics(2))"
}
finally {
    if ($null -ne $reportDocument) { $reportDocument.Close(0) }
    if ($null -ne $wordApp) { $wordApp.Quit() }
}
