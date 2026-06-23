; JMate Inno Setup 安装脚本
; 构建顺序：
;   1. 运行 pyinstaller --clean --noconfirm --distpath dist_upx JMate.spec，
;      生成 dist_upx\JMate\JMate.exe（onedir 目录）。
;   2. 确认 installer\node-v24.16.0-x64.msi 存在。
;   3. 使用 Inno Setup 6 编译本文件，安装包输出到 installer_output。
;
; 安装器只收集已存在的文件，不会替你运行 PyInstaller；如修改 distpath、
; 程序名或重新切换 onefile，必须同步修改 [Files] 中的 Source。

[Setup]
; 安装程序基本信息及“程序和功能”中的显示名称。
AppName=JMate
AppVersion=1.0.0
; {autopf} 在 64 位安装模式下解析为 64 位 Program Files。
DefaultDirName={autopf}\JMate
DefaultGroupName=JMate
; 输出目录相对于本 .iss 文件所在目录。
OutputDir=installer_output
OutputBaseFilename=JMateSetup
Compression=lzma
SolidCompression=yes
; 使用 64 位安装模式；如需严格拒绝非 x64 系统，可另外设置 ArchitecturesAllowed。
ArchitecturesInstallIn64BitMode=x64
; Node MSI 和公共桌面快捷方式需要管理员权限。
PrivilegesRequired=admin

[Files]
; 复制 PyInstaller onedir 的完整目录。Qt 插件、Python DLL 和 _internal 目录
; 都必须保留相对结构，不能只复制 JMate.exe。
Source: "dist_upx\JMate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; dontcopy 表示不直接安装到 {app}；InstallNode 调用 ExtractTemporaryFile 后，
; MSI 才会被释放到 {tmp} 并交给 msiexec 静默安装。
Source: "installer\node-v24.16.0-x64.msi"; Flags: dontcopy

[Icons]
; 开始菜单组快捷方式和所有用户桌面快捷方式。
Name: "{group}\JMate"; Filename: "{app}\JMate.exe"
Name: "{commondesktop}\JMate"; Filename: "{app}\JMate.exe"

[Run]
; 非静默安装完成后显示“启动 JMate”选项；nowait 不等待桌面程序退出。
Filename: "{app}\JMate.exe"; Description: "启动 JMate"; Flags: nowait postinstall skipifsilent

[Code]
const
  ; JMate 接受的最低 Node.js 版本。
  MinNodeMajor = 24;
  MinNodeMinor = 0;
  MinNodePatch = 0;
  ; 更新内置 MSI 时，文件名、[Files] Source 和展示版本必须一起修改。
  NodeMsiName = 'node-v24.16.0-x64.msi';
  BundleNodeVersion = '24.16.0';

function GetNodeExePath(var NodePath: string): Boolean;
var
  InstallPath: string;
begin
  Result := False;

  ; Node 官方 MSI 通常在 HKLM\SOFTWARE\Node.js 写入 InstallPath。
  ; 依次检查 64 位机器级、当前安装视图和当前用户注册表。
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

function GetNodeVersion(
  NodePath: string;
  var VersionText: string;
  var Major, Minor, Patch: Cardinal
): Boolean;
var
  VersionMS, VersionLS: Cardinal;
begin
  Result := False;
  VersionText := '';

  ; 直接读取 node.exe 的 Windows 文件版本，不创建控制台进程。
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
  ; 按 major → minor → patch 顺序比较语义版本。
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

  ; 将 dontcopy 文件释放到安装器临时目录。
  ExtractTemporaryFile(NodeMsiName);
  NodeMsiPath := ExpandConstant('{tmp}\') + NodeMsiName;

  if not FileExists(NodeMsiPath) then
  begin
    MsgBox('Node.js 安装包释放失败：' + NodeMsiPath, mbError, MB_OK);
    Exit;
  end;

  ; /qn：无 UI；/norestart：不允许 MSI 自行重启系统。
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

  ; MSI 退出码 0 表示本次安装成功。3010（需要重启）当前仍按失败处理；
  ; 如需支持该退出码，应设置 NeedsRestart 并单独处理。
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
  ; 返回空字符串表示允许继续安装；返回错误文本会中止安装并展示文本。
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
      ; 找到 node.exe 但无法读取版本时，允许用户用内置 MSI 修复。
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
    ; 没有注册表记录时，不通过 PATH 猜测，直接询问是否安装内置版本。
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
