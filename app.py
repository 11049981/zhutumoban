from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from processor import process_image
import tempfile
import time
from threading import Thread
import schedule
import base64
import shutil

app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 配置上传文件夹
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'psd_files' not in request.files or 'template_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    template_file = request.files['template_file']
    psd_files = request.files.getlist('psd_files')
    
    if template_file.filename == '' or not psd_files:
        return jsonify({'error': 'No file selected'}), 400

    results = []
    template_path = None
    temp_dir = None
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 保存模板文件
        template_path = os.path.join(temp_dir, secure_filename(template_file.filename))
        template_file.save(template_path)
        
        # 处理每个PSD文件
        for psd_file in psd_files:
            try:
                # 获取原始文件名和目录
                filename = secure_filename(psd_file.filename)
                file_dir = os.path.dirname(os.path.abspath(filename))
                
                # 设置临时和输出路径
                temp_psd_path = os.path.join(temp_dir, filename)
                output_filename = f'processed_{os.path.splitext(filename)[0]}.png'
                
                # 如果目录不存在，使用当前目录
                if not file_dir or file_dir == '.':
                    file_dir = os.getcwd()
                    
                output_path = os.path.join(file_dir, output_filename)
                
                # 保存上传的PSD文件
                psd_file.save(temp_psd_path)
                
                # 处理图片
                process_image(temp_psd_path, template_path, output_path)
                
                # 读取处理后的图片用于预览
                with open(output_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # 添加成功结果
                results.append({
                    'filename': filename,
                    'success': True,
                    'output_path': output_path,
                    'preview_data': f'data:image/png;base64,{img_data}'
                })
                
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")  # 添加错误日志
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e)
                })
            
            finally:
                # 清理临时PSD文件
                if os.path.exists(temp_psd_path):
                    os.remove(temp_psd_path)
        
        return jsonify({'results': results})
        
    except Exception as e:
        print(f"处理请求时出错: {str(e)}")  # 添加错误日志
        return jsonify({'error': str(e)}), 500
        
    finally:
        # 清理临时文件和目录
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# 添加静态文件清理任务
def cleanup_old_files():
    folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        # 删除超过5分钟的文件
        if os.path.getmtime(file_path) < time.time() - 300:
            os.remove(file_path)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 在主程序中添加定时清理
if __name__ == '__main__':
    # 每5分钟运行一次清理
    schedule.every(5).minutes.do(cleanup_old_files)
    
    # 在后台运行清理任务
    cleanup_thread = Thread(target=run_schedule)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # 运行Flask应用
    app.run(debug=True, port=5000) 