"""
Excel智能体主应用
整合所有模块，提供WebSocket和HTTP接口
"""
import os
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import openai
from excel_preprocessor import ExcelPreprocessor
from nlp_parser import NLPParser
from code_generator import CodeGenerator
from code_executor import CodeExecutor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'excel-agent-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化组件
preprocessor = ExcelPreprocessor(knowledge_base_path="knowledge_base")
nlp_parser = None  # 将在启动时初始化
code_generator = CodeGenerator()

# 存储当前会话数据
session_data = {}


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/initialize', methods=['POST'])
def initialize():
    """初始化API密钥和加载文件"""
    data = request.json
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'API密钥不能为空'}), 400
    
    try:
        # 初始化NLP解析器
        global nlp_parser
        nlp_parser = NLPParser(api_key=api_key)
        
        # 加载所有Excel文件
        files = preprocessor.load_all_files()
        files_info = preprocessor.get_all_files_info()
        
        return jsonify({
            'success': True,
            'files': list(files.keys()),
            'files_info': files_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
def query():
    """处理查询请求"""
    data = request.json
    query_text = data.get('query')
    session_id = data.get('session_id', 'default')
    
    if not query_text:
        return jsonify({'error': '查询不能为空'}), 400
    
    if not nlp_parser:
        return jsonify({'error': '请先初始化API密钥'}), 400
    
    try:
        # 获取可用文件信息
        files_info = preprocessor.get_all_files_info()
        
        if not files_info:
            return jsonify({'error': '没有可用的Excel文件，请先上传文件到knowledge_base目录'}), 400
        
        # 解析查询
        intent = nlp_parser.parse_query(query_text, files_info)
        
        # 获取目标文件
        target_file = intent.get('target_file')
        if not target_file or target_file not in preprocessor.processed_files:
            return jsonify({'error': f'找不到目标文件: {target_file}'}), 400
        
        df = preprocessor.processed_files[target_file]
        file_path = preprocessor.file_metadata[target_file]['path']
        
        # 设置文件路径属性
        df.attrs['file_path'] = file_path
        
        # 生成代码
        generated_code = code_generator.generate_code(intent, file_path, df)
        used_columns = code_generator.get_used_columns()
        
        # 执行代码
        executor = CodeExecutor(file_path)
        execution_result = executor.execute(generated_code)
        
        # 保存会话数据
        session_data[session_id] = {
            'intent': intent,
            'code': generated_code,
            'result': execution_result,
            'used_columns': used_columns
        }
        
        return jsonify({
            'success': True,
            'intent': intent,
            'code': generated_code,
            'execution': execution_result,
            'used_columns': used_columns,
            'target_file': target_file
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """WebSocket连接"""
    print('客户端已连接')
    emit('connected', {'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket断开"""
    print('客户端已断开')


@socketio.on('voice_query')
def handle_voice_query(data):
    """处理语音查询"""
    query_text = data.get('query')
    session_id = data.get('session_id', 'default')
    
    if not query_text:
        emit('error', {'message': '查询不能为空'})
        return
    
    if not nlp_parser:
        emit('error', {'message': '请先初始化API密钥'})
        return
    
    try:
        # 发送处理中状态
        emit('processing', {'message': '正在处理您的查询...'})
        
        # 获取可用文件信息
        files_info = preprocessor.get_all_files_info()
        
        if not files_info:
            emit('error', {'message': '没有可用的Excel文件'})
            return
        
        # 解析查询
        intent = nlp_parser.parse_query(query_text, files_info)
        emit('intent_parsed', {'intent': intent})
        
        # 获取目标文件
        target_file = intent.get('target_file')
        if not target_file or target_file not in preprocessor.processed_files:
            emit('error', {'message': f'找不到目标文件: {target_file}'})
            return
        
        df = preprocessor.processed_files[target_file]
        file_path = preprocessor.file_metadata[target_file]['path']
        df.attrs['file_path'] = file_path
        
        # 生成代码
        generated_code = code_generator.generate_code(intent, file_path, df)
        used_columns = code_generator.get_used_columns()
        emit('code_generated', {'code': generated_code, 'used_columns': used_columns})
        
        # 执行代码
        executor = CodeExecutor(file_path)
        execution_result = executor.execute(generated_code)
        emit('execution_complete', {
            'result': execution_result,
            'used_columns': used_columns,
            'target_file': target_file
        })
        
        # 保存会话数据
        session_data[session_id] = {
            'intent': intent,
            'code': generated_code,
            'result': execution_result,
            'used_columns': used_columns
        }
        
    except Exception as e:
        emit('error', {'message': str(e)})


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传Excel文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名不能为空'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': '只支持Excel文件(.xlsx, .xls)'}), 400
    
    try:
        # 保存文件
        os.makedirs('knowledge_base', exist_ok=True)
        file_path = os.path.join('knowledge_base', file.filename)
        file.save(file_path)
        
        # 加载文件
        df = preprocessor.load_excel_file(file_path)
        file_info = preprocessor.get_file_info(file.filename)
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'file_name': file.filename,
            'file_info': file_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def list_files():
    """列出所有文件"""
    files_info = preprocessor.get_all_files_info()
    return jsonify({
        'files': list(files_info.keys()),
        'files_info': files_info
    })


if __name__ == '__main__':
    # 确保知识库目录存在
    os.makedirs('knowledge_base', exist_ok=True)
    
    # 启动服务器
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

