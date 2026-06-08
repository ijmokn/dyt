[Setup]
AppName=JMate
AppVersion=1.0.0
DefaultDirName={autopf}\JMate
DefaultGroupName=JMate
OutputDir=installer_output
OutputBaseFilename=JMateSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Files]
Source: "dist\JMate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installer\node-v24.16.0-x64.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\JMate"; Filename: "{app}\JMate.exe"
Name: "{commondesktop}\JMate"; Filename: "{app}\JMate.exe"

[Run]
Filename: "{app}\JMate.exe"; Description: "启动 JMate"; Flags: nowait postinstall skipifsilent

[Code]
const
  MinNodeMajor = 24;
  MinNodeMinor = 0;
  MinNodePatch = 0;

function GetNodeExePath(var NodePath: string): Boolean;
var
  InstallPath: string;
begin
  Result := False;

  if RegQueryStringValue(HKLM64, 'SOFTWARE\Node.js', 'InstallPath', InstallPath) then
  begin
    NodePath := AddBackslash(InstallPath) + 'node.exe';
    if FileExists(NodePath) then
    begin
      Result := True;
      Exit;
    end;
  end;

  if RegQueryStringValue(HKLM, 'SOFTWARE\Node.js', 'InstallPath', InstallPath) then
  begin
    NodePath := AddBackslash(InstallPath) + 'node.exe';
    if FileExists(NodePath) then
    begin
      Result := True;
      Exit;
    end;
  end;

  if RegQueryStringValue(HKCU, 'SOFTWARE\Node.js', 'InstallPath', InstallPath) then
  begin
    NodePath := AddBackslash(InstallPath) + 'node.exe';
    if FileExists(NodePath) then
    begin
      Result := True;
      Exit;
    end;
  end;
end;

function IsNodeVersionEnough(NodePath: string): Boolean;
var
  VersionMS, VersionLS: Cardinal;
  Major, Minor, Patch: Cardinal;
begin
  Result := False;

  if not GetVersionNumbers(NodePath, VersionMS, VersionLS) then
    Exit;

  Major := VersionMS shr 16;
  Minor := VersionMS and $FFFF;
  Patch := VersionLS shr 16;

  if Major > MinNodeMajor then
    Result := True
  else if Major = MinNodeMajor then
  begin
    if Minor > MinNodeMinor then
      Result := True
    else if Minor = MinNodeMinor then
    begin
      if Patch >= MinNodePatch then
        Result := True;
    end;
  end;
end;

function NeedInstallNode(): Boolean;
var
  NodePath: string;
begin
  Result := True;

  if GetNodeExePath(NodePath) then
  begin
    if IsNodeVersionEnough(NodePath) then
      Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';

  if NeedInstallNode() then
  begin
    if MsgBox(
      '检测到当前系统未安装 Node.js，或 Node.js 版本低于 ' +
      IntToStr(MinNodeMajor) + '.' + IntToStr(MinNodeMinor) + '.' + IntToStr(MinNodePatch) +
      '。' + #13#10#13#10 +
      'JMate 需要 Node.js 才能正常运行。是否现在安装 Node.js？',
      mbConfirmation,
      MB_YESNO
    ) = IDYES then
    begin
      if not Exec(
        'msiexec.exe',
        '/i "' + ExpandConstant('{tmp}\node-v24.16.0-x64.msi') + '" /qn /norestart',
        '',
        SW_HIDE,
        ewWaitUntilTerminated,
        ResultCode
      ) then
      begin
        Result := 'Node.js 安装程序启动失败，请手动安装 Node.js 后再安装 JMate。';
        Exit;
      end;

      if ResultCode <> 0 then
      begin
        Result := 'Node.js 安装失败，请手动安装 Node.js 后再安装 JMate。错误码：' + IntToStr(ResultCode);
        Exit;
      end;
    end
    else
    begin
      Result := '已取消安装。JMate 需要 Node.js 环境才能正常运行。';
      Exit;
    end;
  end;
end;