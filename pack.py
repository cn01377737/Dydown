import sys
import os
from PyInstaller.__main__ import run

def build_win11():
    # Windows 11专属打包配置
    opts = [
        '--name=DyDown',
        '--onefile',
        '--windowed',
        '--icon=dydown/icon.ico',
        '--add-data=ffmpeg;ffmpeg',
        '--add-data=config.yml;.',
        '--target-architecture=64bit',
        '--osx-bundle-identifier=com.dydown.client',
        '--runtime-tmpdir=.',
        '--hidden-import=PyQt6.sip',
        '--hidden-import=requests',
        '--hidden-import=yt_dlp'
    ]
    
    # Windows 11兼容性配置
    opts += [
        '--uac-admin',
        '--manifest=manifest.xml'
    ]
    
    # 添加主入口
    opts.append('dydown/main.py')
    
    # 执行打包
    run(opts)

if __name__ == '__main__':
    if '--win11' in sys.argv:
        build_win11()
        print('Windows 11独立运行包构建完成')
        '--icon=dydown/icon.ico',