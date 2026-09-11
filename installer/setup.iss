; Inno Setup Script for JARVIS VoiceOS
; Generates: JARVIS-Setup.exe

[Setup]
AppId={{D37E8862-A8E2-4C10-9FE0-E6C8F2C2C64B}
AppName=JARVIS VoiceOS
AppVersion=1.0.0
AppPublisher=JARVIS AI
AppPublisherURL=https://www.voiceos.com/
AppSupportURL=https://www.voiceos.com/
AppUpdatesURL=https://www.voiceos.com/
DefaultDirName={autopf}\JARVIS
DefaultGroupName=JARVIS VoiceOS
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=JARVIS-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start JARVIS automatically with Windows"; GroupDescription: "Startup:"

[Files]
Source: "dist\JARVIS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\JARVIS VoiceOS"; Filename: "{app}\JARVIS.exe"
Name: "{group}\{cm:UninstallProgram,JARVIS VoiceOS}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\JARVIS VoiceOS"; Filename: "{app}\JARVIS.exe"; Tasks: desktopicon
Name: "{userstartup}\JARVIS VoiceOS"; Filename: "{app}\JARVIS.exe"; Tasks: startupicon

[Run]
Filename: "{app}\JARVIS.exe"; Description: "{cm:LaunchProgram,JARVIS VoiceOS}"; Flags: nowait postinstall skipifsilent
