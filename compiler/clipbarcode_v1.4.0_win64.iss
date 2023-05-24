#define MyAppName "ClipBarcode"
#define MyAppVersion "1.4.0"
#define MyOutputBaseFilename "clipbarcode_v1.4.0_win64"
#define MyAppPublisher "Vin�cius Costa"
#define MyAppURL "https://github.com/viniciusccosta"
#define MyAppExeName "ClipBarcode.exe"

[Setup]
AppId={{0E3273EB-F520-4E39-8E16-F7538AE44197}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userappdata}\..\Local\Programs\{#MyAppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename={#MyOutputBaseFilename}
SetupIconFile=..\dist\main\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\icon.ico

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "tesseract-ocr-w64-setup-v5.2.0.20220712.exe"; DestDir: "{app}"; Flags: dontcopy
Source: "vcredist_x64.exe"; DestDir: "{app}"; Flags: dontcopy
Source: "..\dist\main\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.config"
Type: filesandordirs; Name: "{app}\app.log"
Type: filesandordirs; Name: "{app}\history"

[Messages]
SetupAppTitle    = {#MyAppName} {#MyAppVersion}
SetupWindowTitle = {#MyAppName} {#MyAppVersion}

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  ExtractTemporaryFile('tesseract-ocr-w64-setup-v5.2.0.20220712.exe');
  Exec(ExpandConstant('{tmp}\tesseract-ocr-w64-setup-v5.2.0.20220712.exe'), '', '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode);

  ExtractTemporaryFile('vcredist_x64.exe');
  Exec(ExpandConstant('{tmp}\vcredist_x64.exe'), '', '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode);
end;