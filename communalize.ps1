param([Parameter(Mandatory=$true)][string]$Source,
      [string]$Name="",
      [string]$Owner="",
      [switch]$Public,
      [switch]$Private,
      [switch]$Local)
$ErrorActionPreference="Stop"
$python=(Get-Command python -ErrorAction SilentlyContinue).Source
if(-not $python){throw "Install Python 3 and Git first"}
$argsList=@("$PSScriptRoot/communalize.py",$Source)
if($Name){$argsList+=@("--name",$Name)}
if($Owner){$argsList+=@("--owner",$Owner)}
if($Public){$argsList+="--public"}elseif($Private){$argsList+="--private"}else{$argsList+="--local"}
& $python @argsList
if($LASTEXITCODE -ne 0){throw "Conversion failed, exit=$LASTEXITCODE"}
