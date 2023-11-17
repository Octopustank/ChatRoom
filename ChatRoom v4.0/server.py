'''  ChatRoom  主程序  '''
''' v 4.0 - brand new era '''

from flask import Flask, make_response, render_template, request, redirect, send_file, flash, session
import datetime as dt
import os
from urllib.parse import quote
from init import *

IP = "0.0.0.0"
PORT = 80

app = Flask("chat_room")
app.config['JSON_AS_ASCII'] = False
app.secret_key = "hard"


# 主页
@app.route("/")
def index():
    addr = request.remote_addr
    if session.get("account") is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        userid = USERDB[session.get("account")][0]
        HOUR_NOW = dt.datetime.now().hour
        if HOUR_NOW in range(5,12):
            return render_template("index.html", greetings="🌅 Good Morning", userid=userid, addr=addr)
        elif HOUR_NOW in range(12,18):
            return render_template("index.html", greetings="🌞 Good Afternoon", userid=userid, addr=addr)
        elif HOUR_NOW in range(18,22):
            return render_template("index.html", greetings="🌇 Good Evening", userid=userid, addr=addr)
        else:
            return render_template("index.html", greetings="🌙 Good Night", userid=userid, addr=addr)

# 聊天主页面
@app.route("/chatroom/")          
def main():
    addr = request.remote_addr
    if session.get("account") is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        userid = USERDB[session.get("account")][0]
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
    if session.get("account") is None:            # 用户未注册，重定向至注册页面
        return redirect('/login')
    else:
        if request.method == 'GET':
            return render_template('send.html')
        if request.method == 'POST':
            addr = request.remote_addr
            userid = session.get("name")
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
            else: return render_template("login.html", python_alert="Incorrect password.")
        else: return render_template("login.html", python_alert="Account does not exist.")
                
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
            return render_template("register1.html", python_alert="ERROR: At least one column is empty!")
        if not(len(username) in range(3,17)) or not (len(pwd) in range(8,31)):
            print(pwd,pwd2,username)
            return render_template("register1.html", python_alert="ERROR: Invalid length of column!")
        if username in UIDB:
            return render_template("register1.html", python_alert="ERROR: Account name already in use!")
        for char in username:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ _1234567890":
                return render_template("register1.html", python_alert="ERROR: Invalid character(s) found in column!")
        if pwd != pwd2:
            return render_template("register1.html", python_alert="ERROR: Password mismatched!")
        
        uid = max(UIDB.values())+1
        UIDB[username] = uid
        write_file(UIDFILE,UIDB)
        USERDB.append([username, pwd])
        write_file(USERFILE,USERDB)
        return redirect("/login")

# 消息历史记录
@app.route("/chatroom/backlog")
def backlog():
    addr = request.remote_addr
    userid = session.get("account")
    return render_template("backlog.html", userid=userid, addr=addr, lst=BACK_LOG_LST, n=BACK_LOG_LEN)

#文件传输
@app.route("/chatroom/downloads", methods=["GET","POST"])
def filesending():
    addr = request.remote_addr
    userid = session.get("account")
    if request.method=="GET":#查看/下载(GET)
        file = request.args.get("file")
        if file is not None:#下载
            path = os.path.join(PATH_FILES, file)
            if os.path.isfile(path):#文件存在、是文件
                file_name = quote(file)#把文件名转码
                file_response = send_file(path, as_attachment=True, attachment_filename=file_name)
                file_response.headers["Content-Disposition"] += ";filename*=utf-8''{}".format(file_name)#把文件名转回UTF-8
                return file_response
            else:#查看
                flash("文件不存在")
                init_file_sending()#文件被删除，选择重新加载
                return redirect('/chatroom/downloads')
        else:#未传值
            return render_template("downloads.html", file_list=FILE_LIST[::-1], addr=addr, userid=userid)
    else:#上传文件(GET)
        file = request.files["file"]
        if addr in USER_LST:
            userid = USER_LST[addr]
        else:userid = "Unknown"
        if file:
            file_path, file_name = check_filename(PATH_FILES, file.filename)
            file.save(file_path)
            time = dt.datetime.now().strftime("%m/%d %H:%M:%S")
            FILE_LIST.append([file_name, time, addr, userid])
            write_file(PATH_FILE_JS, FILE_LIST)
            flash(f"文件上传为{file_name}")
            return redirect('/chatroom/downloads')
        else:
            flash("请选择文件！")
            return redirect('/chatroom/downloads')

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

########################################
if __name__ =="__main__":
    PATH = init_path()
    DATA_LST, LOGFILE, UIDB, UIDFILE, USERDB, USERFILE, floor = init_file()
    BACK_LOG_LST, BACK_LOG_LEN = init_backlog()
    PATH_FILE_JS, PATH_FILES, FILE_LIST = init_file_sending()
    app.run(host=IP, port=PORT, debug=True)
