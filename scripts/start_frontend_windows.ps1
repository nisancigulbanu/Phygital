$root = "C:\Users\gulba\Desktop\Phygital\mobile"
$flutter = "C:\src\flutter\flutter\bin\flutter.bat"
$stdout = "C:\Users\gulba\Desktop\Phygital\frontend_detached.out.log"
$stderr = "C:\Users\gulba\Desktop\Phygital\frontend_detached.err.log"

Set-Location $root
Start-Process -FilePath $flutter `
  -ArgumentList "run", "-d", "windows", "--no-resident" `
  -WorkingDirectory $root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr
