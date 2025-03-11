!include MUI2.nsh
!include nsDialogs.nsh
!include LogicLib.nsh
!include WinMessages.nsh
!include FileFunc.nsh

; 设置中文语言包
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装程序名称
Name "DouYin Downloader"
OutFile "DouYinDownloader_Setup.exe"

; 默认安装目录
InstallDir "$PROGRAMFILES\DouYin Downloader"

; 添加FFmpeg路径到环境变量
Section "FFmpeg"
  SetOutPath "$INSTDIR\ffmpeg"
  File /r "installer\ffmpeg\*"
  EnVar::SetHKCU
  EnVar::AddValue "Path" "$INSTDIR\ffmpeg\bin"
SectionEnd

; 创建桌面快捷方式
Section "Shortcut"
  CreateShortcut "$DESKTOP\DouYin Downloader.lnk" "$INSTDIR\DouYinCommand.exe"
SectionEnd

; 更新检查模块
Section "Updater"
  SetOutPath "$INSTDIR"
  File "updater.exe"
SectionEnd

; 安装界面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 卸载程序
Section "Uninstall"
  Delete "$DESKTOP\DouYin Downloader.lnk"
  RMDir /r "$INSTDIR"
SectionEnd
 
