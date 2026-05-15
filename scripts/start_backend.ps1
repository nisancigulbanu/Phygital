$root = "C:\Users\gulba\Desktop\Phygital"
$python = "C:\msys64\ucrt64\bin\python.exe"
$stdout = Join-Path $root "backend_detached.out.log"
$stderr = Join-Path $root "backend_detached.err.log"

Set-Location $root
Start-Process -FilePath $python `
  -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000" `
  -WorkingDirectory $root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr
