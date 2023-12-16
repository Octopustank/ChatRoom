'''  服务器主程序  '''
''' v 4.3 - support more online-view filetype & improving code '''

from flask import Flask, render_template, request, redirect, send_file, flash, session, make_response
import datetime as dt
import os
from urllib.parse import quote
from init import *

IP = "0.0.0.0"
PORT = 80

FILE_MAXSIZE = 500 * 1024 * 1024 # 云盘文件大小限制：500MB

app = Flask("chat_room")
app.config['JSON_AS_ASCII'] = False
app.secret_key = "hard"


# 主页
@app.route("/")
def index():
    addr = request.remote_addr
    uid = session.get("account")
    if uid is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        userid = USERDB[uid][0]
        HOUR_NOW = dt.datetime.now().hour
        if HOUR_NOW in range(5,12):
            return render_template("index.html", HOUR_NOW=HOUR_NOW, greetings="🌅 上午好", userid=userid, addr=addr)
        elif HOUR_NOW in range(12,18):
            return render_template("index.html", HOUR_NOW=HOUR_NOW, greetings="🌞 下午好", userid=userid, addr=addr)
        elif HOUR_NOW in range(18,22):
            return render_template("index.html", HOUR_NOW=HOUR_NOW, greetings="🌇 晚上好", userid=userid, addr=addr)
        else:
            return render_template("index.html", HOUR_NOW=HOUR_NOW, greetings="🌙 晚上好", userid=userid, addr=addr)

# 聊天主页面
@app.route("/chatroom/")          
def main():
    addr = request.remote_addr
    uid = session.get("account")
    if uid is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        userid = USERDB[uid][0]
        if len(DATA_LST) == 0:
            return render_template("chatroom.html", 
            DATA_LST=DATA_LST, addr=addr, userid=userid, python_message="- 还没有消息记录  快来抢沙发吧 -")
        else:
            return render_template("chatroom.html", 
            DATA_LST=DATA_LST, addr=addr,  userid=userid, python_message="- 你看到我的底线了 -")

# 发送窗口
@app.route("/chatroom/send", methods=["GET","POST"])          
def send():
    global floor
    uid = session.get("account")
    if uid is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        if request.method == 'GET':
            return render_template('send.html')
        if request.method == 'POST':
            addr = request.remote_addr
            userid = USERDB[uid][0]
            name = request.form.get("name")
            text = request.form.get("text")
            if not all([name,text]):
                return render_template('send.html', python_alert="用户名/内容不能为空！")
            TIME_NOW = dt.datetime.now().strftime("%m/%d %H:%M:%S")
            if len(DATA_LST) != 0:
                floor = DATA_LST[-1][1]+1

            DATA_LST.append([TIME_NOW, floor, name, addr, userid, text])
            write_file(LOGFILE,DATA_LST)
            return render_template('send.html', python_hint="发送成功！",last=name)

# 登录
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == 'GET':
        if session.get("account") is not None:
            return redirect('/')
        else:
            return render_template("login.html")
    if request.method == 'POST':
        username = request.form.get("userid")
        pwd = request.form.get("pwd")
        if username in UIDB:
            uid = UIDB[username]
            if pwd == USERDB[uid][1]:
                session['account'] = uid
                return redirect('/')
            else: return render_template("login.html", python_alert="用户名或密码不正确！")
        else: return render_template("login.html", python_alert="用户不存在！")
                
# 登出
@app.route("/logout")
def logout():
    session.pop("account")
    return redirect("/login")

# 新用户注册
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == 'GET':
        if session.get("account") is not None:
            return redirect('/')
        else:
            return render_template("register1.html")
    if request.method == 'POST':
        username = request.form.get("userid")
        pwd = request.form.get("pwd")
        pwd2 = request.form.get("pwd2")
        # 用户名密码是否符合要求
        if username is None or pwd is None or pwd2 is None:
            return render_template("register1.html", python_alert="错误：请完成所有必填项。")
        if not(len(username) in range(3,17)) or not (len(pwd) in range(8,31)):
            print(pwd,pwd2,username)
            return render_template("register1.html", python_alert="错误：长度不符。")
        if username in UIDB:
            return render_template("register1.html", python_alert="错误：用户已存在！")
        for char in username:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ _1234567890":
                return render_template("register1.html", python_alert="错误：使用了非法字符。")
        if pwd != pwd2:
            return render_template("register1.html", python_alert="两次输入的密码不一致！")
        
        uid = max(UIDB.values())+1
        UIDB[username] = uid
        write_file(UIDFILE,UIDB)
        USERDB.append([username, pwd])
        write_file(USERFILE,USERDB)
        return redirect("/login")

# 用户管理
@app.route("/account",methods=["GET","POST"])
def account():
    if request.method == 'GET':
        uid = session.get("account")
        if uid is None:
            return redirect('/login')
        else:
            userid = USERDB[uid][0]
            pwd = USERDB[uid][1]
            return render_template("account.html",userid=userid, uid=uid)
    if request.method == 'POST':
        uid = session.get("account")
        userid = USERDB[uid][0]
        
        username = request.form.get("userid")
        pwd = request.form.get("pwd")
        pwd2 = request.form.get("pwd2")
        # 用户名密码是否符合要求
        if username is None or pwd is None or pwd2 is None:
            return render_template("account.html",userid=userid, uid=uid, python_alert="错误：请完成所有必填项。")
        if not(len(username) in range(3,17)) or not (len(pwd) in range(8,31)):
            print(pwd,pwd2,username)
            return render_template("account.html",userid=userid, uid=uid, python_alert="错误：长度不符。")
        for char in username:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ _1234567890":
                return render_template("account.html",userid=userid, uid=uid, python_alert="错误：使用了非法字符。")
        if pwd != pwd2:
            return render_template("account.html",userid=userid, uid=uid, python_alert="两次输入的密码不一致！")
        
        UIDB.pop(userid)
        UIDB[username] = uid
        write_file(UIDFILE,UIDB)
        USERDB[uid]=[username, pwd]
        write_file(USERFILE,USERDB)
        return redirect("/logout")

# 消息历史记录
@app.route("/chatroom/backlog")
def backlog():
    addr = request.remote_addr
    userid = session.get("account")
    return render_template("backlog.html", userid=userid, addr=addr, lst=BACK_LOG_LST, n=BACK_LOG_LEN)

# 云盘
@app.route("/cloud")
def filesending():
    uid = session.get("account")
    if uid is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        username = USERDB[uid][0]
        file = request.args.get("file")
        if file is not None:#下载
            path = os.path.join(PATH_FILES, file)
            if os.path.isfile(path):#文件存在、是文件
                file_name = quote(file)#把文件名转码
                file_response = send_file(path, as_attachment=True, download_name=file_name)
                file_response.headers["Content-Disposition"] += ";filename*=utf-8''{}".format(file_name)#把文件名转回UTF-8
                return file_response
            else:#查看
                flash("文件已不存在。请询问网络管理员")
                init_file_sending() #文件被删除，选择重新加载
                return redirect('/cloud')
        else:#未传值
            return render_template("cloud.html", file_list=FILE_LIST[::-1], userid=username)

# 传文件到云盘
@app.route("/upload", methods=["POST"])
def upload():
    uid = session.get("account")
    if uid is None: # 用户未注册，重定向至注册页面
            return redirect('/login')
    
    file = request.files["file"]
    if not file: # 没选择文件就进行了请求
        flash("请选择一个文件")
        return redirect("/cloud")
    
    if file.content_length > FILE_MAXSIZE: # 限制文件大小
        flash(f"文件大于{FILE_MAXSIZE // 1024 // 1024}MB，上传失败")
        return redirect("/cloud")
    
    username = USERDB[uid][0]
    file_path, file_name = check_filename(PATH_FILES, file.filename) # 防止重名
    file.save(file_path)
    
    time = dt.datetime.now().strftime("%m/%d %H:%M")
   
    file_alias = file_name          # 存入文件别名（治标不治本的防文本框溢出）
    for j in range(len(file_name.split('.')[:-1])):
        if j % 18==0:
            if file_name[j] != '.':         # 防吞扩展名
                file_alias = file_alias[:j] + ' ' + file_alias[j:]
                j += 1
            else:
                j -= 1
                file_alias = file_alias[:j] + ' ' + file_alias[j:]
                
    FILE_LIST.append([file_name, time, username, uid, file_alias])
    write_file(PATH_FILE_JS, FILE_LIST)
    flash(f"文件上传为: {file_alias}")
    return redirect('/cloud')

# 在线文件预览源
@app.route('/file/<path:file>')  
def serve_file(file):
    # 获取文件扩展名来确定文件类型
    file = os.path.join(PATH_FILES, file)
    extension = os.path.splitext(file)[1].lower()  
  
    # 根据文件类型返回适当的响应  
    if extension in ['.jpg', '.jpeg', '.png', '.gif']:  
        # 处理图片文件  
        with open(file, 'rb') as f:  
            response = make_response(f.read())  
            response.headers['Content-Type'] = 'image/jpeg' # 根据实际文件类型设置正确的 Content-Type  
            return response  

    elif extension in ['.mp4', '.avi', '.mov', '.mp3']:  
        # 处理视频文件  
        with open(file, 'rb') as f:  
            response = make_response(f.read())  
            response.headers['Content-Type'] = 'video/mp4' 
            return response
        
    else:
        # 处理其他文件，视为文本
        try:
            with open(file, 'r', encoding="utf-8") as f:  
                response = make_response(f.read())  
                response.headers['Content-Type'] = 'text/plain; charset=utf-8'
                return response
        except:
            # 处理其他情况
            return "Unsupported file type", 400

# 视频在线预览
@app.route("/play")
def play():
    uid = session.get("account")
    if uid is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        file = request.args.get("file")
        if file is not None:
            path = os.path.join(PATH_FILES, file)
            if os.path.isfile(path):
                return render_template("play.html", fileurl=f"/file/{file}", pyfilename = file)
            else:
                init_file_sending()
                return render_template("play.html", fileurl="", pyfilename = "未选择文件.")
        else:
            return render_template("play.html", fileurl="", pyfilename = "未选择文件.")

#检视模板文件用(trap_door)
@app.route("/query", methods=["GET"])
def query():
    query = request.args.get("file")
    return render_template(query)

#刷新数据用(trap_door)
@app.route("/chatroom/refresh")
def refresh():
    global USER_LST
    mode = request.args.get("mode")
    if mode == "users":
        USER_LST = read_file(USERFILE)
        return f"刷新用户列表成功<p>{USER_LST}"
    elif mode == "files":
        init_file_sending()
        return f"刷新文件列表成功<p>{'<p>'.join(list(map(str,FILE_LIST)))}"
    return redirect('/chatroom/')

@app.errorhandler(404)  # 传入错误码作为参数状态
def error404(error):  # 接受错误作为参数
    return render_template("404.html"), 404  

########################################
if __name__ =="__main__":
    PATH = init_path()
    DATA_LST, LOGFILE, UIDB, UIDFILE, USERDB, USERFILE, floor = init_file()
    BACK_LOG_LST, BACK_LOG_LEN = init_backlog()
    PATH_FILE_JS, PATH_FILES, FILE_LIST = init_file_sending()
    app.run(host=IP, port=PORT, debug=True)
    #app.run(host=IP, port=PORT, debug=True, ssl_context = ('ssl/littlecorner.space_bundle.crt', 'ssl/littlecorner.space.key'))
