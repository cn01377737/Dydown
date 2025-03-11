[Setup]
AppName=DyDown
AllowNoIcons=yes
SilentInstall=normal
SilentUninstall=normal
AppVersion=1.0
DefaultDirName={pf}\DyDown
DefaultGroupName=DyDown
UninstallDisplayIcon={app}\DyDown.exe
OutputDir=.
OutputBaseFilename=DyDownSetup
PrivilegesRequired=admin

; 64位安装程序配置
[Setup]
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; 安装过程动画效果
WizardImageFile=installer.bmp
WizardSmallImageFile=installer_small.bmp
WizardImageStretch=no
WizardStyle=modern

[Files]
Source: "build\DyDown\DyDown.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.rtf"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DyDown"; Filename: "{app}\DyDown.exe"
Name: "{userdesktop}\DyDown"; Filename: "{app}\DyDown.exe"

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: string; ValueName: "DyDownPath"; ValueData: "{app}"; Flags: preservestringtype

[Code]
var
  CustomPage: TWizardPage;
  InstallPathEdit: TNewEdit;
  DesktopShortcutCheckBox: TNewCheckBox;
  AddToPathCheckBox: TNewCheckBox;

procedure InitializeWizard;
begin
  // 创建自定义配置页
  CustomPage := CreateCustomPage(wpWelcome, '自定义配置', '请选择安装选项');

  // 添加安装路径输入框
  InstallPathEdit := TNewEdit.Create(WizardForm);
  InstallPathEdit.Parent := CustomPage.Surface;
  InstallPathEdit.Top := 16;
  InstallPathEdit.Width := CustomPage.SurfaceWidth;
  InstallPathEdit.Text := ExpandConstant('{pf}\DyDown');
  InstallPathEdit.Prompt := '安装路径';

  // 添加桌面快捷方式复选框
  DesktopShortcutCheckBox := TNewCheckBox.Create(WizardForm);
  DesktopShortcutCheckBox.Parent := CustomPage.Surface;
  DesktopShortcutCheckBox.Caption := '创建桌面快捷方式';
  DesktopShortcutCheckBox.Top := InstallPathEdit.Top + InstallPathEdit.Height + 16;
  DesktopShortcutCheckBox.Width := CustomPage.SurfaceWidth;
  DesktopShortcutCheckBox.Checked := true;

  // 添加PATH环境变量复选框
  AddToPathCheckBox := TNewCheckBox.Create(WizardForm);
  AddToPathCheckBox.Parent := CustomPage.Surface;
  AddToPathCheckBox.Caption := '添加到PATH环境变量';
  AddToPathCheckBox.Top := DesktopShortcutCheckBox.Top + DesktopShortcutCheckBox.Height + 16;
  AddToPathCheckBox.Width := CustomPage.SurfaceWidth;
  AddToPathCheckBox.Checked := true;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if AddToPathCheckBox.Checked then
    begin
      RegWriteStringValue(HKCU, 'Environment', 'DyDownPath', ExpandConstant('{app}'));
    end;
    // 验证安装结果
    if not WizardSilent then
    begin
      if DesktopShortcutCheckBox.Checked and not FileExists(ExpandConstant('{userdesktop}\DyDown.lnk')) then
      begin
        MsgBox('桌面快捷方式创建失败！', mbError, MB_OK);
      end;
      if not RegKeyExists(HKLM, 'Software\Dydown') then
      begin
        MsgBox('注册表项创建失败！', mbError, MB_OK);
      end;
    end;
  end;
end;