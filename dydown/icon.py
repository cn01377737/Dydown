from PIL import Image
import os
import subprocess

try:
    # 加载SVG源文件
    svg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.svg'))
    # 转换SVG到PNG
    png_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'temp_icon.png'))
    subprocess.run(['C:\\Program Files\\Inkscape\\bin\\inkscape.exe', svg_path, '--export-type=png', f'--export-filename={png_path}'], check=True)
    img = Image.open(png_path)
    
    # 生成多尺寸ICO文件
    ico_sizes = [(16,16), (32,32), (48,48), (256,256)]
    img.save(os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.ico')), format='ICO', sizes=ico_sizes)
    print('ICO文件生成成功！')
except Exception as e:
    print(f'图标生成失败: {str(e)}')
    raise
finally:
    if os.path.exists(png_path):
        os.remove(png_path)