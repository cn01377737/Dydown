; 安装程序初始定义
!define PRODUCT_NAME "抖音视频下载器"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "DyDown"
!define PRODUCT_WEB_SITE "https://github.com/your-repo/dydown"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\dydown.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; 引入现代界面
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

; 安装程序图标
!define MUI_ICON "..\dydown\icon.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; 安装界面设置
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\modern-wizard.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\modern-header.bmp"

; 安装界面中文设置
!define MUI_LANGDLL_REGISTRY_ROOT "HKLM" 
!define MUI_LANGDLL_REGISTRY_KEY "Software\${PRODUCT_NAME}" 
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

; 界面配置
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 卸载界面配置
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 语言文件
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; 输出文件名
OutFile "DyDown-Setup-${PRODUCT_VERSION}.exe"
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
InstallDir "$PROGRAMFILES\DyDown"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; 安装前检查
Function .onInit
  ; 检查是否已安装
  ReadRegStr $R0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
  StrCmp $R0 "" done
  
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "检测到已安装${PRODUCT_NAME}，是否先卸载？" \
    IDOK uninst
  Abort
  
uninst:
  ExecWait '$R0 _?=$INSTDIR'
  
done:
  ; 检查Python环境
  ReadRegStr $R0 HKLM "SOFTWARE\Python\PythonCore\3.8\InstallPath" ""
  StrCmp $R0 "" noPython
  Goto checkFFmpeg
  
noPython:
  MessageBox MB_YESNO|MB_ICONQUESTION \
    "未检测到Python 3.8或更高版本，是否下载安装？" \
    IDYES downloadPython
  Abort
  
downloadPython:
  ExecShell "open" "https://www.python.org/downloads/"
  Abort
  
checkFFmpeg:
  ; 检查FFmpeg
  ReadEnvStr $R0 "PATH"
  ${StrStr} $R0 $R0 "ffmpeg"
  StrCmp $R0 "" noFFmpeg done
  
noFFmpeg:
  MessageBox MB_OK|MB_ICONINFORMATION \
    "未检测到FFmpeg，将在安装过程中自动安装。"
FunctionEnd

; 安装部分
Section "主程序 (必需)" SEC01
  SectionIn RO
  SetOutPath "$INSTDIR"
  
  ; 复制主程序文件
  File /r "..\dydown\*.*"
  
  ; 复制FFmpeg
  SetOutPath "$INSTDIR\ffmpeg"
  File /r "ffmpeg\*.*"
  
  ; 添加FFmpeg到环境变量
  EnVar::SetHKLM
  EnVar::AddValue "PATH" "$INSTDIR\ffmpeg\bin"
  
  ; 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\DyDown"
  CreateShortCut "$SMPROGRAMS\DyDown\抖音视频下载器.lnk" "$INSTDIR\dydown.exe"
  CreateShortCut "$SMPROGRAMS\DyDown\卸载.lnk" "$INSTDIR\uninst.exe"
  
  ; 创建桌面快捷方式
  CreateShortCut "$DESKTOP\抖音视频下载器.lnk" "$INSTDIR\dydown.exe"
  
  ; 写入注册表
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\dydown.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\dydown.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\uninst.exe"
SectionEnd

Section "更新检查模块" SEC02
  SetOutPath "$INSTDIR"
  File "..\dydown\updater.py"
SectionEnd

; 区段描述
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "安装主程序和必要组件"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} "安装自动更新检查模块"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; 卸载部分
Section Uninstall
  ; 删除程序文件
  RMDir /r "$INSTDIR"
  
  ; 删除开始菜单快捷方式
  Delete "$SMPROGRAMS\DyDown\*.*"
  RMDir "$SMPROGRAMS\DyDown"
  
  ; 删除桌面快捷方式
  Delete "$DESKTOP\抖音视频下载器.lnk"
  
  ; 删除注册表项
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  ; 从环境变量中移除FFmpeg
  EnVar::SetHKLM
  EnVar::DeleteValue "PATH" "$INSTDIR\ffmpeg\bin"
  
  SetAutoClose true
SectionEnd 