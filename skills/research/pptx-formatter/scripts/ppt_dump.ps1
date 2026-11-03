# Open the deck read-only in PowerPoint (COM) and dump the EFFECTIVE formatting (inheritance resolved),
# shape boxes and line-by-line text (Shift+Enter line ends marked <BR>) to JSON. The deck is never modified.
# Usage (via ppt_dump.sh): powershell -File ppt_dump.ps1 <deck.pptx win path> <out.json win path>
param([string]$Deck, [string]$Out)
$ErrorActionPreference = "Continue"
$was = @(Get-Process POWERPNT -ErrorAction SilentlyContinue).Count -gt 0
$ppt = New-Object -ComObject PowerPoint.Application
$p = $ppt.Presentations.Open($Deck, $true, $false, $false)
$res = [ordered]@{ w = $p.PageSetup.SlideWidth; h = $p.PageSetup.SlideHeight; slides = @() }

function TextOf($tf2) {
  $paras = @()
  $tr = $tf2.TextRange
  for ($i = 1; $i -le $tr.Paragraphs().Count; $i++) {
    $pg = $tr.Paragraphs($i)
    $runs = @()
    for ($j = 1; $j -le $pg.Runs().Count; $j++) {
      $r = $pg.Runs($j)
      $t = $r.Text -replace "[\r\n\v]", ""
      if ($t.Trim().Length -eq 0) { continue }
      $runs += [ordered]@{ t = $t; f = $r.Font.Name; fe = $r.Font.NameFarEast; sz = $r.Font.Size;
                           b = ($r.Font.Bold -eq -1); c = $r.Font.Fill.ForeColor.RGB }
    }
    if ($runs.Count -eq 0) { continue }
    $lines = @()
    for ($k = 1; $k -le $pg.Lines().Count; $k++) { $lines += ($pg.Lines($k).Text -replace "[\r\n]", "" -replace "\v", "<BR>") }
    $paras += [ordered]@{ lvl = $pg.ParagraphFormat.IndentLevel; al = $pg.ParagraphFormat.Alignment; lines = $lines;
                          bullet = ($pg.ParagraphFormat.Bullet.Visible -eq -1); runs = $runs }
  }
  return $paras
}

function ShapeOf($sh, $grp) {
  $o = [ordered]@{ id = $sh.Id; name = $sh.Name; grp = $grp; type = $sh.Type; ph = $null;
                   x = $sh.Left; y = $sh.Top; w = $sh.Width; h = $sh.Height; paras = @() }
  try { if ($sh.Type -eq 14) { $o.ph = $sh.PlaceholderFormat.Type } } catch {}
  try {
    if ($sh.HasTextFrame -eq -1 -and $sh.TextFrame2.HasText -eq -1) {
      $o.paras = @(TextOf $sh.TextFrame2)
      $tr = $sh.TextFrame2.TextRange
      $o.bx = $tr.BoundLeft; $o.by = $tr.BoundTop; $o.bw = $tr.BoundWidth; $o.bh = $tr.BoundHeight
      $o.autosize = $sh.TextFrame2.AutoSize
    }
  } catch {}
  return $o
}

foreach ($s in $p.Slides) {
  $shapes = @()
  foreach ($sh in $s.Shapes) {
    if ($sh.Type -eq 6) {  # group
      $shapes += ShapeOf $sh $null
      foreach ($g in $sh.GroupItems) { $shapes += ShapeOf $g $sh.Name }
    } elseif ($sh.HasTable -eq -1) {
      $shapes += ShapeOf $sh $null
      $tb = $sh.Table
      for ($r = 1; $r -le $tb.Rows.Count; $r++) { for ($c = 1; $c -le $tb.Columns.Count; $c++) {
        $cs = $tb.Cell($r, $c).Shape
        $o = [ordered]@{ id = "$($sh.Id)/r$r" + "c$c"; name = "$($sh.Name) [$r,$c]"; grp = $sh.Name; type = "cell"; ph = $null;
                         x = $sh.Left; y = $sh.Top; w = 0; h = 0; paras = @() }
        try { if ($cs.TextFrame2.HasText -eq -1) { $o.paras = @(TextOf $cs.TextFrame2) } } catch {}
        $shapes += $o
      } }
    } else { $shapes += ShapeOf $sh $null }
  }
  $res.slides += [ordered]@{ n = $s.SlideIndex; layout = $s.CustomLayout.Name; hidden = ($s.SlideShowTransition.Hidden -eq -1); shapes = $shapes }
}
$p.Close(); if (-not $was) { $ppt.Quit() }   # never close a PowerPoint the user already had open
[System.IO.File]::WriteAllText($Out, ($res | ConvertTo-Json -Depth 12 -Compress), [System.Text.UTF8Encoding]::new($false))
Write-Output "dumped $($res.slides.Count) slides"
