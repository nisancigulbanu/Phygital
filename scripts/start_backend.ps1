$root = "C:\Users\gulba\Desktop\Phygital"
$stdout = Join-Path $root "backend_detached.out.log"
$stderr = Join-Path $root "backend_detached.err.log"

function Resolve-BackendPython {
  if ($env:PHYGITAL_PYTHON -and (Test-Path $env:PHYGITAL_PYTHON)) {
    return $env:PHYGITAL_PYTHON
  }

  $candidates = @(
    (Join-Path $root ".venv\Scripts\python.exe"),
    (Join-Path $root ".venv\bin\python.exe")
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCommand) {
    return $pythonCommand.Source
  }

  throw "Python bulunamadi. PHYGITAL_PYTHON ayarlayin veya proje icinde .venv olusturun."
}

$python = Resolve-BackendPython

Set-Location $root
Start-Process -FilePath $python `
  -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000" `
  -WorkingDirectory $root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr
