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
Source: "dist_upx\JMate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installer\node-v24.16.0-x64.msi"; Flags: dontcopy

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
  NodeMsiName = 'node-v24.16.0-x64.msi';
  BundleNodeVersion = '24.16.0';

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

function GetNodeVersion(NodePath: string; var VersionText: string; var Major, Minor, Patch: Cardinal): Boolean;
var
  VersionMS, VersionLS: Cardinal;
begin
  Result := False;
  VersionText := '';

  if not GetVersionNumbers(NodePath, VersionMS, VersionLS) then
    Exit;

  Major := VersionMS shr 16;
  Minor := VersionMS and $FFFF;
  Patch := VersionLS shr 16;

  VersionText :=
    IntToStr(Major) + '.' +
    IntToStr(Minor) + '.' +
    IntToStr(Patch);

  Result := True;
end;

function IsVersionEnough(Major, Minor, Patch: Cardinal): Boolean;
begin
  Result := False;

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

function InstallNode(): Boolean;
var
  ResultCode: Integer;
  NodeMsiPath: String;
begin
  Result := False;

  ExtractTemporaryFile(NodeMsiName);
  NodeMsiPath := ExpandConstant('{tmp}\') + NodeMsiName;

  if not FileExists(NodeMsiPath) then
  begin
    MsgBox('Node.js 安装包释放失败：' + NodeMsiPath, mbError, MB_OK);
    Exit;
  end;

  if not Exec(
    'msiexec.exe',
    '/i "' + NodeMsiPath + '" /qn /norestart',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    MsgBox('Node.js 安装程序启动失败，请手动安装 Node.js 后再安装 JMate。', mbError, MB_OK);
    Exit;
  end;

  if ResultCode <> 0 then
  begin
    MsgBox('Node.js 安装失败，错误码：' + IntToStr(ResultCode), mbError, MB_OK);
    Exit;
  end;

  Result := True;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  NodePath: string;
  VersionText: string;
  Major, Minor, Patch: Cardinal;
begin
  Result := '';

  if GetNodeExePath(NodePath) then
  begin
    if GetNodeVersion(NodePath, VersionText, Major, Minor, Patch) then
    begin
      if IsVersionEnough(Major, Minor, Patch) then
      begin
        MsgBox(
          '检测到本机已安装 Node.js，当前版本为：v' + VersionText + '。' + #13#10#13#10 +
          '该版本满足 JMate 的运行要求，将继续安装 JMate。',
          mbInformation,
          MB_OK
        );
        Exit;
      end
      else
      begin
        if MsgBox(
          '检测到本机已安装 Node.js，当前版本为：v' + VersionText + '。' + #13#10#13#10 +
          'JMate 要求 Node.js 版本不低于 v' +
          IntToStr(MinNodeMajor) + '.' + IntToStr(MinNodeMinor) + '.' + IntToStr(MinNodePatch) + '。' + #13#10#13#10 +
          '是否现在升级到安装包内置的 Node.js v' + BundleNodeVersion + '？',
          mbConfirmation,
          MB_YESNO
        ) = IDYES then
        begin
          if not InstallNode() then
          begin
            Result := 'Node.js 自动升级失败，请手动安装 Node.js v' + BundleNodeVersion + ' 后再安装 JMate。';
            Exit;
          end;
        end
        else
        begin
          Result := '已取消安装。JMate 需要 Node.js v' +
            IntToStr(MinNodeMajor) + '.' + IntToStr(MinNodeMinor) + '.' + IntToStr(MinNodePatch) +
            ' 或更高版本才能正常运行。';
          Exit;
        end;
      end;
    end
    else
    begin
      if MsgBox(
        '检测到本机已安装 Node.js，但无法读取版本号。' + #13#10#13#10 +
        '是否现在安装/修复为 Node.js v' + BundleNodeVersion + '？',
        mbConfirmation,
        MB_YESNO
      ) = IDYES then
      begin
        if not InstallNode() then
        begin
          Result := 'Node.js 自动安装失败，请手动安装 Node.js v' + BundleNodeVersion + ' 后再安装 JMate。';
          Exit;
        end;
      end
      else
      begin
        Result := '已取消安装。无法确认 Node.js 版本是否满足要求。';
        Exit;
      end;
    end;
  end
  else
  begin
    if MsgBox(
      '未检测到本机安装 Node.js。' + #13#10#13#10 +
      'JMate 需要 Node.js 才能正常运行，是否现在安装内置的 Node.js v' + BundleNodeVersion + '？',
      mbConfirmation,
      MB_YESNO
    ) = IDYES then
    begin
      if not InstallNode() then
      begin
        Result := 'Node.js 自动安装失败，请手动安装 Node.js v' + BundleNodeVersion + ' 后再安装 JMate。';
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