import os
import json
import shutil
import requests
import re
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, session, request, jsonify, flash, send_file, abort
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)
root_path = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(root_path, "data")
exam_folder = os.path.join(data_folder, "exam")
log_folder = os.path.join(data_folder, "exam_log")

load_dotenv()

# Google OAuth 설정
flow = Flow.from_client_secrets_file(
    os.path.join(root_path, os.getenv("GOOGLE_LOGIN_SECRETS_FILE")),
    scopes=[ "https://www.googleapis.com/auth/userinfo.email", "openid", "https://www.googleapis.com/auth/userinfo.profile" ],
    redirect_uri=os.getenv("GOOGLE_LOGIN_REDIRECT_URI")
)

# TXT 파일 로드 함수
def parse_question(text):
    questions = text.strip().split('\n\n')  # 빈 줄을 기준으로 문제 분리
    result = []
    for question in questions:
        lines = question.strip().split('\n')
        if len(lines) < 2:
            continue
        question_text = lines[0]
        options = []
        answer_line = lines[-1]
        
        for line in lines[1:-1]:
            options.append(line.strip())
        
        answer = answer_line.replace("Answer:", "").strip().split(",")
        answer = [a.strip() for a in answer]
        
        result.append({
            "question": question_text,
            "item": options,
            "answer": answer
        })
    
    return result

# userlist.json 으로 사용자 계정 점검
def check_email_in_userlist(user_info):
    file_path = os.path.join(data_folder, "userlist.json")
    if not os.path.exists(file_path):
        return False
    with open(file_path, 'r', encoding='utf-8') as file:
        userlist = json.load(file)
    for user in userlist:
        if user.get("email") == user_info['email']:
            if 'user' not in session:
                session['user'] = {
                    'id': user_info['email'],
                    'name': user.get("name"),
                    'nickname': user_info['name'],
                    'picture': user_info['picture']
                }
            return True
    return False

# data 폴더에 등록된 시험 리스트
def get_exam_list():
    exam_list = []
    file_info = {}
    
    for f in os.listdir(exam_folder):
        if f.endswith(".txt"):
            file_path = os.path.join(exam_folder, f)
            exam_type = os.path.splitext(f)[0]  # 확장자 제거한 파일명
            
            # file_info.json에 저장된 데이터 조회
            file_info_path = os.path.join(log_folder, exam_type, 'file_info.json')
            if os.path.exists(file_info_path):
                with open(file_info_path, 'r', encoding='utf-8') as info_file:
                    file_info = json.load(info_file)
            else:
                created_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S")  # 생성일시
                file_size = os.path.getsize(file_path)  # 파일 크기 (바이트)
                
                # 파일 내용 읽어서 문제 개수 카운트
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    questions = parse_question(content)  # 문제 파싱
                    question_count = len(questions)  # 문제 개수
                
                file_info = {
                    "name": exam_type,
                    "created": created_time,
                    "size": file_size,
                    "question_count": question_count,
                    "user_id": "",
                    "user_name": ""
                }
                
            exam_list.append(file_info)

    # 파일명을 기준으로 정렬
    exam_list.sort(key=lambda x: x["name"])
    return exam_list
    
# 모든 페이지 접근 전에 로그인 확인
@app.before_request
def check_login():
    allowed_routes = ['login', 'logout', 'login_using_google', 'login_callback']    #예외 페이지
    if request.endpoint and request.endpoint.startswith('static'):
        return None #/static 폴더를 제외
    if 'user' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

# 메인 화면(시험 리스트)
@app.route('/')
def dashboard():
    return render_template("dashboard.html", files=get_exam_list())

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.clear()
        NAS_URL = os.getenv("SYNOLOGY_NAS_URL")
        username = request.form['username']
        password = request.form['password']
        params = {
            "api": "SYNO.API.Auth",
            "version": "3",
            "method": "login",
            "account": username,
            "passwd": password,
            "session": "FileStation",
            "format": "sid"
        }
        response = requests.get(f"{NAS_URL}/webapi/auth.cgi", params=params)
        data = response.json()
        
        if data.get("success"):
            session['user'] = {
                'id': username,
                'name': username,
                'email': '',
                'picture': ''
            }
            return redirect(url_for('dashboard'))
        else:
            flash("아이디 또는 비밀번호가 일치하지 않습니다.", "danger")
            return redirect(url_for('login'))
    
    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 구글 계정으로 로그인
@app.route("/login/google")
def login_using_google():
    session.clear()
    auth_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    return redirect(auth_url)

# 구글 계정으로 로그인 - Callback
@app.route("/login/callback")
def login_callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token if credentials.refresh_token else session.get("credentials", {}).get("refresh_token"),
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    
    if "credentials" not in session:
        return redirect(url_for("login"))
    
    credentials = Credentials(**session["credentials"])
    from googleapiclient.discovery import build
    service = build("oauth2", "v2", credentials=credentials)
    user_info = service.userinfo().get().execute()
    
    if check_email_in_userlist(user_info):        
        return redirect(url_for('dashboard'))
    else:
        session.clear()
        flash("사용이 허가되지 않았습니다!", "danger")
        return redirect(url_for('login'))    

# 시험 보기
@app.route('/exam/<exam_type>')
def index(exam_type):
    return render_template('index.html', exam_type=exam_type)

# 시험 데이터
@app.route('/exam/<exam_type>/<media_type>', methods=['GET'])
def get_exam_json(exam_type, media_type):
    filepath = os.path.join(exam_folder, f'{exam_type}.txt')
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            txt_data = file.read()
        if media_type == 'json':            
            parsed_data = parse_question(txt_data)
            return jsonify(parsed_data) if parsed_data else jsonify({"error": "No valid questions found."})
        else:
            return txt_data
    return jsonify({"error": "File not found"}), 404

# 시험 데이터 - 다운로드
@app.route('/download/<exam_type>/<media_type>', methods=['GET'])
def download_exam(exam_type, media_type):
    filepath = os.path.join(exam_folder, f'{exam_type}.txt')
    if not os.path.exists(filepath):
        abort(404, description="File not found")
    
    with open(filepath, "r", encoding="utf-8") as file:
        txt_data = file.read()
    if media_type == 'json':            
        parsed_data = parse_question(txt_data)
        json_buffer = io.BytesIO()
        json_buffer.write(json.dumps(parsed_data, ensure_ascii=False, indent=4).encode('utf-8'))
        json_buffer.seek(0)
        
        return send_file(json_buffer, as_attachment=True, mimetype='application/json', download_name=f'{exam_type}.json')
    else:
        return send_file(filepath, as_attachment=True, mimetype='text/plain', download_name=f'{exam_type}.txt')

# 업로드 페이지
@app.route('/upload')
def upload():
    return render_template('upload.html')

# 업로드 실행
@app.route('/upload/<exam_type>/<overwrite>', methods=['POST'])
def upload_file(exam_type, overwrite):
    try:
        filename = f"{exam_type}.txt" 
        
        # 파일 내용 읽기
        file_content = request.data.decode("utf-8")
        
        # 텍스트 파일 파싱
        parsed_data = parse_question(file_content)
        
        # 텍스트 파일 형식 점검
        for question in parsed_data:
            if not question.get("question") or not question.get("item") or not question.get("answer"):
                return jsonify({"is_saved": False, "msg_txt": "텍스트 파일 형식이 올바르지 않습니다!"})
        
        # 폴더 생성
        file_path = os.path.join(exam_folder, filename)
        
        # 동일한 파일이 있는지 확인
        if os.path.exists(file_path) and not overwrite == 'true':
            return jsonify({"ask_overwrite": True})  # 클라이언트에 덮어쓰기 여부 요청
        
        # 세션에서 name과 email 가져오기 (없으면 기본값 설정)
        user = session.get("user", {})
        name = user.get("name", "unknown")
        id = user.get("id", "unknown")
              
        # 폴더 생성
        logfile_path = os.path.join(log_folder, exam_type)
        if not os.path.exists(logfile_path):
            os.makedirs(logfile_path)
        
        # 타임스탬프 파일명 생성        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]  # 밀리초까지 포함 (마지막 3자리만 사용)
        formatted_filename = f"{timestamp}@@{id}@@{name}.txt"
        logfile = os.path.join(logfile_path, formatted_filename)

        # 파일 저장
        with open(logfile, "w", encoding="utf-8") as f:
            f.write(request.data.decode("utf-8"))
        
        shutil.copy2(logfile, file_path)
        
        # 파일 생성일/생성자 정보 저장
        # JSON 데이터 구성
        file_size = os.path.getsize(file_path)  # 파일 크기 (바이트 단위)
        
        # 파일 내용 읽어서 문제 개수 카운트
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            questions = parse_question(content)  # 문제 파싱
            question_count = len(questions)  # 문제 개수
        
        file_info = {
            "name": exam_type,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 생성일시,
            "size": file_size,
            "question_count": question_count,
            "user_id": id,
            "user_name": name
        }
        
        file_info_path = os.path.join(logfile_path, 'file_info.json')
        # JSON 파일 저장 (존재하면 덮어쓰기)
        with open(file_info_path, 'w', encoding='utf-8') as f:
            json.dump(file_info, f, ensure_ascii=False, indent=4)

        return jsonify({"is_saved": True, "msg_txt": "저장되었습니다!"})
    except Exception as e:
        return jsonify({"is_saved": False, "msg_txt": f"업로드 실패: {str(e)}"})

# 삭제 페이지
@app.route('/delete')
def delete():    
    return render_template("delete.html", files=get_exam_list())

# 파일 삭제
@app.route('/delete/<exam_type>', methods=['POST'])
def delete_file(exam_type):    
    try:
        filename = os.path.join(exam_folder, f'{exam_type}.txt')        
        os.remove(filename)  # 또는 os.unlink(file_path)
        return jsonify({"is_deleted": True, "msg_txt": "삭제되었습니다!"})
    except FileNotFoundError:       
        return jsonify({"is_deleted": False, "msg_txt": f"{filename} 파일을 찾을 수 없습니다."})
    except PermissionError:     
        return jsonify({"is_deleted": False, "msg_txt": f"{filename} 파일을 삭제할 권한이 없습니다."})
    except Exception as e:
        return jsonify({"is_deleted": False, "msg_txt": f"삭제 실패: {str(e)}"})

if __name__ == '__main__':
    app.run(host='localhost', port=5000, ssl_context="adhoc")
