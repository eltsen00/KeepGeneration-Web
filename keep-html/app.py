import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from KeepSultan import KeepSultan
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制

DEFAULT_AVATAR = 'static/default_avatar.png'
MAP_PRESETS = {
    'SYSU英东体育场': 'static/maps/map4.png',
    '珠江南岸': 'static/maps/map5.png',
    'SYSU大圈': 'static/maps/map1.png',
    'SYSU小圈': 'static/maps/map2.png',
    'SYSU中轴线': 'static/maps/map3.png'
}

# 创建必要目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 默认配置
DEFAULT_CONFIG = {
    "template": "static/default_template.png",
    "map": "static/maps/map1.png",
    "username": "Keep User",
    "date": datetime.now().strftime("%Y/%m/%d"),
    "end_time": datetime.now().strftime("%H:%M"),
    "location": "广州市",
    "weather": "多云",
    "temperature": "20°C",
    "total_km": [4.02, 4.3],
    "sport_time": ["00:23:00", "00:25:00"],
    "total_time": ["00:27:00", "00:31:00"],
    "cumulative_climb": [90, 96],
    "average_cadence": [90, 99],
    "exercise_load": [70, 90]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 处理文件上传
        map_selection = request.form.get('map_preset')
        custom_map = handle_upload('custom_map','map')
        
        # 确定最终地图路径
        map_path = MAP_PRESETS.get(map_selection) if map_selection else None
        if custom_map:
            map_path = custom_map
        
        # 处理头像文件
        avatar_path = handle_upload('avatar', 'avatar') or DEFAULT_AVATAR

        # 获取表单参数
        form_data = {
            'username': request.form.get('username', DEFAULT_CONFIG['username']),
            'date': request.form.get('date', DEFAULT_CONFIG['date']),
            'location': request.form.get('location', DEFAULT_CONFIG['location']),
            'weather': request.form.get('weather', DEFAULT_CONFIG['weather']),
            'temperature': request.form.get('temperature', DEFAULT_CONFIG['temperature']),
            'end_time': request.form.get('end_time', DEFAULT_CONFIG['end_time']),
            'total_km': [
                float(request.form.get('total_km_min', DEFAULT_CONFIG['total_km'][0])),
                float(request.form.get('total_km_max', DEFAULT_CONFIG['total_km'][1]))
            ],
            'sport_time': [
                request.form.get('sport_time_min', DEFAULT_CONFIG['sport_time'][0]),
                request.form.get('sport_time_max', DEFAULT_CONFIG['sport_time'][1])
            ],
            'total_time': [
                request.form.get('total_time_min', DEFAULT_CONFIG['total_time'][0]),
                request.form.get('total_time_max', DEFAULT_CONFIG['total_time'][1])
            ],
            'cumulative_climb': [
                int(request.form.get('cumulative_climb_min', DEFAULT_CONFIG['cumulative_climb'][0])),
                int(request.form.get('cumulative_climb_max', DEFAULT_CONFIG['cumulative_climb'][1]))
            ],
            'average_cadence': [
                int(request.form.get('average_cadence_min', DEFAULT_CONFIG['average_cadence'][0])),
                int(request.form.get('average_cadence_max', DEFAULT_CONFIG['average_cadence'][1]))
            ],
            'exercise_load': [
                int(request.form.get('exercise_load_min', DEFAULT_CONFIG['exercise_load'][0])),
                int(request.form.get('exercise_load_max', DEFAULT_CONFIG['exercise_load'][1]))
            ]
        }

        # 生成图片
        output_filename = f"result_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        try:
            generate_image(
                DEFAULT_CONFIG['template'],
                map_path or DEFAULT_CONFIG['map'],
                avatar_path,
                form_data,
                output_path
            )
            return redirect(url_for('preview', filename=output_filename))
        except Exception as e:
            return render_template('error.html', error=str(e))

    return render_template('index.html', default_config=DEFAULT_CONFIG,map_presets=MAP_PRESETS.keys())

def handle_upload(field_name, file_type):
    if field_name not in request.files:
        return None
    file = request.files[field_name]
    if file.filename == '':
        return None
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{file_type}_{datetime.now().timestamp()}.png")
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        return save_path
    return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def generate_image(template_path, map_path, avatar_path, params, output_path):
    ks = KeepSultan()
    
    # 配置参数
    ks.configs.update({
        'template': template_path,
        'map': map_path,
        'avatar': avatar_path,
        'username': params['username'],
        'date': params['date'].replace('-', '/'),
        'location': params['location'],
        'weather': params['weather'],
        'temperature': params['temperature'],
        'end_time': params['end_time'],
        'total_km': params['total_km'],
        'sport_time': params['sport_time'],
        'total_time': params['total_time'],
        'cumulative_climb': params['cumulative_climb'],
        'average_cadence': params['average_cadence'],
        'exercise_load': params['exercise_load']
    })
    
    # 生成图片
    ks.process()
    ks.save(output_path)

@app.route('/preview/<filename>')
def preview(filename):
    return render_template('preview.html', 
                          image_url=url_for('static', filename=f'output/{filename}'),
                          download_url=url_for('download', filename=filename))

@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True,
        download_name=f"keep_result_{datetime.now().strftime('%Y%m%d')}.png"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=False)