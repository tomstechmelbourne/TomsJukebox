; Tom's Jukebox - Windows installer (Inno Setup 6)
#define AppVer "0.9.6-beta"
[Setup]
AppId={{6C0F5B8E-7A44-4D7C-9B1E-3A5D7C11B0E1}
AppName=Tom's Jukebox
AppVersion={#AppVer}
AppVerName=Tom's Jukebox {#AppVer}
AppPublisher=Tom's Technology Solutions
AppPublisherURL=mailto:tomstechmelbourne@gmail.com
DefaultDirName={autopf}\Tom's Jukebox
DefaultGroupName=Tom's Jukebox
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\Output
OutputBaseFilename=TomsJukebox-{#AppVer}-Setup
SetupIconFile=..\assets\app_icon.ico
UninstallDisplayIcon={app}\TomsJukebox.exe
UninstallDisplayName=Tom's Jukebox
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
VersionInfoVersion=0.9.6.0
VersionInfoCompany=Tom's Technology Solutions
VersionInfoDescription=Tom's Jukebox Setup
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop shortcut / Lối tắt ngoài Desktop"; GroupDescription: "Shortcuts / Lối tắt:"

[Files]
Source: "..\dist\TomsJukebox\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\HUONG_DAN.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Tom's Jukebox"; Filename: "{app}\TomsJukebox.exe"; WorkingDir: "{app}"
Name: "{group}\Hướng Dẫn (HUONG_DAN)"; Filename: "{app}\HUONG_DAN.txt"
Name: "{group}\Uninstall Tom's Jukebox"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Tom's Jukebox"; Filename: "{app}\TomsJukebox.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\TomsJukebox.exe"; Description: "Open Tom's Jukebox now / Mở Tom's Jukebox ngay"; Flags: nowait postinstall skipifsilent

; Your music, recordings, playlists and settings live in %APPDATA%\Tom's Jukebox and Music\Tom's Jukebox.
; They are NOT removed when the program is uninstalled.
