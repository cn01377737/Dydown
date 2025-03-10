import os
import shutil
import subprocess
import requests
import zipfile
from pathlib import Path

def download_ffmpeg():
    """下载FFmpeg"""
    print("正在下载FFmpeg...")
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    response = requests.get(ffmpeg_url, stream=True)
    
    with open("ffmpeg.zip", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print("正在解压FFmpeg...")
    with zipfile.ZipFile("ffmpeg.zip", "r") as zip_ref:
        zip_ref.extractall("installer/ffmpeg")
    
    os.remove("ffmpeg.zip")

def copy_program_files():
    """复制程序文件到构建目录"""
    print("正在复制程序文件...")
    
    # 创建构建目录
    os.makedirs("build", exist_ok=True)
    
    # 复制Python文件
    shutil.copytree("dydown", "build/dydown", dirs_exist_ok=True)
    
    # 复制图标和其他资源
    shutil.copy("dydown/icon.ico", "build/")
    shutil.copy("LICENSE", "build/")

def build_installer():
    """构建安装程序"""
    print("正在构建安装程序...")
    
    # 确保NSIS已安装
    nsis_path = r"C:\Program Files (x86)\NSIS\makensis.exe"
    if not os.path.exists(nsis_path):
        print("错误：未找到NSIS，请先安装NSIS。")
        return False
    
    # 运行NSIS脚本
    subprocess.run([nsis_path, "installer/installer.nsi"])
    return True

def main():
    # 创建必要的目录
    os.makedirs("installer/ffmpeg", exist_ok=True)
    os.makedirs("build", exist_ok=True)
    
    try:
        # 下载FFmpeg
        if not os.path.exists("installer/ffmpeg/bin/ffmpeg.exe"):
            download_ffmpeg()
        
        # 复制程序文件
        copy_program_files()
        
        # 构建安装程序
        if build_installer():
            print("安装程序构建完成！")
        else:
            print("安装程序构建失败！")
    
    except Exception as e:
        print(f"构建过程出错：{e}")
    
    finally:
        # 清理构建目录
        if os.path.exists("build"):
            shutil.rmtree("build")

if __name__ == "__main__":
    main() 