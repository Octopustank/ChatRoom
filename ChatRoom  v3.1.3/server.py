from flask import Flask, render_template, request, redirect, send_file, flash
import datetime as dt
import json as js
import os
from urllib.parse import quote
import sys
#################### 判断Pyhon版本来判断使用场景 ####################
PY_VERSION = sys.version.split(" ")[0]
print(f"[Scene] RUNNING ON Python {PY_VERSION}")
PY_VERSION = sum(map(lambda x:int(x[0])*x[1],zip(PY_VERSION.split("."),[10000,100,1])))
if PY_VERSION >= 30810:
    MODE = 1#非机房
else:
    MODE = 0#机房
print(f"[Scene] USE {['COMPUTER_ROOM','OTHERS'][MODE]}")
### 根据版本进行对应变动 ###
if MODE == 0:
    SEND_FILE = "send_file(path, as_attachment=True, attachment_filename=file_name)"
    IP = "192.168.1.35"
    PORT = 1145
else:
    SEND_FILE = "send_file(path, as_attachment=True, download_name=file_name)"
    IP = "0.0.0.0"
    PORT = 114

#################### 工具函数和初始化 ####################
# 获取工作路径
def init_path():
    global PATH
    path = os.path.abspath(__file__)
    PATH = os.path.dirname(path)
    print(f"[INIT] PATH: {PATH}")

# 当天日志文件和用户文件初始化
def init_file():
    print("[INIT] READ DATA_FILE&USERS")
    global DATA_LST, LOGFILE, USER_LST, USERFILE, floor
    DATA_LST = [];
    init_path()
    DATE_STR = dt.datetime.now().strftime("%y-%m-%d")
    logfiles = os.path.join(PATH,"logfiles")
    LOGFILE = os.path.join(logfiles,f"{DATE_STR}.json")
    bin_ = os.path.join(PATH,"bin")
    USERFILE = os.path.join(bin_,"users.json")
    USER_LST = read_file(USERFILE)
    # 如果当天已存在日志文件，则接着盖楼，否则新建
    if os.path.isfile(LOGFILE):
        DATA_LST = read_file(LOGFILE)
        floor = DATA_LST[-1][1]
        print(f"[INIT] 读取日志:{LOGFILE}")
    else: 
        floor = 1
        print("[INIT] 无已存在日志")
    init_backlog()

# 前7天（最多）历史记录初始化
def init_backlog():
    global BACK_LOG_LST, BACK_LOG_LEN
    print("[INIT] GRAB LOG")
    latest_date = dt.datetime.now()
    former_date = latest_date - dt.timedelta(days=1)
    former_date_str = former_date.strftime("%y-%m-%d")
    logfiles = os.path.join(PATH,"logfiles")
    LOGFILE_p = os.path.join(logfiles,f"{former_date_str}.json")
    BACK_LOG_LST = []
    cnt = 1
    # 循环读日志，条件为日志文件存在且为七天内
    while cnt <=7:
        if os.path.isfile(LOGFILE_p):
            TEMP_LST = read_file(LOGFILE_p)
            TEMP_LST.append(former_date_str)
            BACK_LOG_LST.append(TEMP_LST)
        former_date = former_date - dt.timedelta(days=1)
        former_date_str = former_date.strftime("%y-%m-%d")
        logfiles = os.path.join(PATH,"logfiles")
        LOGFILE_p = os.path.join(logfiles,f"{former_date_str}.json")
        cnt += 1
    BACK_LOG_LEN = len(BACK_LOG_LST)
    print(f"[INIT] {BACK_LOG_LEN} LOGS IN TOTAL")

#初始化文件传输
def init_file_sending():
    global PATH_FILE_JS, PATH_FILES, FILE_LIST
    print("[INIT] READ FILE_LIST")
    path = os.path.join(PATH, "files_sending")
    PATH_FILES = os.path.join(path, "files")
    PATH_FILE_JS = os.path.join(path, "file_data.json")

    FILE_LIST = []
    if os.path.exists(PATH_FILE_JS):
        FILE_LIST = read_file(PATH_FILE_JS)#读上传的文件列表[[filename,user,time]]
        file_list = os.listdir(PATH_FILES)
        p = 0; l = len(FILE_LIST); flag = False#检查文件是否都存在:
        while p < l:
            if not FILE_LIST[p][0] in file_list:
                drop_one = FILE_LIST.pop(p)
                print(f"[FILE_LIST] REMOVE: {drop_one}")
                flag = True
            else: p += 1
            l = len(FILE_LIST)
        l = len(file_list)#检查是否有文件夹中存在但不在列表中的文件:
        for p in range(l):
            files_in_list = list(map(lambda x:x[0],FILE_LIST))#把文件日志中文件名(index=0)取出
            if not file_list[p] in files_in_list:
                FILE_LIST.append([file_list[p],"-/- -:-:-","-.-.-","server"])
                print(f"[FILE_LIST] ADD: {file_list[p]}")
                flag = True
        if flag: write_file(PATH_FILE_JS, FILE_LIST)#若有文件变动，修正该问题

#处理文件名防止重名
def check_filename(path,original_name):
    exist_names = os.listdir(path)
    first_name, last_name = os.path.splitext(original_name)
    name = [first_name, last_name, 0]#文件名各部分和序号(若为0则实际不加)
    make_name = lambda x:x[0]+(f"({str(x[2])})"if x[2]!=0 else "")+x[1]#拼接文件名函数
    while True:
        if not make_name(name) in exist_names:#该文件名独一无二
            break
        name[2]+=1#该文件名已存在，序号增加
    name = make_name(name)
    return os.path.join(path,name), name

# 通用读文件管道
def read_file(F):
    with open(F, 'r', encoding='utf-8') as f:
        data = f.read().encode(encoding='utf-8')
        result = js.loads(data)
    return result

# 通用写文件管道
def write_file(F, data):
    with open(F,"w",encoding="utf-8") as f:
        js.dump(data, f, ensure_ascii=False, indent=True)

#################### Flask主程序 ####################
app = Flask("chat_room")
app.config['JSON_AS_ASCII'] = False
app.secret_key = "hard"

# 聊天主页面
@app.route("/")          
def main():
    addr = request.remote_addr
    if not addr in USER_LST:            # 用户未注册，重定向至注册页面
        return redirect('/register')
    else:
        userid = USER_LST[addr]
        if len(DATA_LST) == 0:
            return render_template("chatroom.html", 
            DATA_LST=DATA_LST, addr=addr, userid=userid, python_message="- 还没有消息记录  快来抢沙发吧 -")
        else:
            return render_template("chatroom.html", 
            DATA_LST=DATA_LST, addr=addr,  userid=userid, python_message="- 你看到我的底线了 -")

# 发送窗口
@app.route("/send", methods=["GET","POST"])          
def send():
    global floor
    if request.method == 'GET':
        return render_template('send.html')
    if request.method == 'POST':
        addr = request.remote_addr
        userid = USER_LST[addr]
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

# 新用户注册
@app.route("/register", methods=["GET","POST"])
def register():
    addr = request.remote_addr
    if request.method == 'GET':
        if addr in USER_LST:
            return redirect('/')
        else:
            return render_template("register.html", addr=addr)
    if request.method == 'POST':
        userid = request.form.get("userid")
        # ID要求判断：长度3~16，合法字符，未被使用
        if userid is None:
            return render_template("register.html", addr=addr, python_alert="ID名不能为空！")
        if not( 2 <= len(userid) <= 4 ):
            return render_template("register.html", addr=addr, python_alert="ID名长度不符合要求！")
        if userid in USER_LST.values():
            return render_template("register.html", addr=addr, python_alert="该ID已被使用！")
        for char in userid:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ":
                return render_template("register.html", addr=addr, python_alert="名称包含非法字符！")

        USER_LST[addr] = userid
        write_file(USERFILE,USER_LST)
        return redirect("/")

# 消息历史记录
@app.route("/backlog")
def backlog():
    addr = request.remote_addr
    userid = USER_LST[addr]
    return render_template("backlog.html", userid=userid, addr=addr, lst=BACK_LOG_LST, n=BACK_LOG_LEN)

#文件传输
@app.route("/downloads", methods=["GET","POST"])
def filesending():
    addr = request.remote_addr
    if request.method=="GET":#查看/下载(GET)
        file = request.args.get("file")
        if file is not None:#下载
            path = os.path.join(PATH_FILES, file)
            if os.path.isfile(path):#文件存在、是文件
                file_name = quote(file)#把文件名转码
##                file_response = send_file(path, as_attachment=True, attachment_filename=file_name)
                file_response = eval(SEND_FILE)
                file_response.headers["Content-Disposition"] += ";filename*=utf-8''{}".format(file_name)#把文件名转回UTF-8
                return file_response
            else:#查看
                flash("文件不存在")
                init_file_sending()#文件被删除，选择重新加载
                return redirect('/downloads')
        else:#未传值
            return render_template("downloads.html", file_list=FILE_LIST[::-1], addr=addr)
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
            return redirect('/downloads')
        else:
            flash("请选择文件！")
            return redirect('/downloads')

#刷新数据用(trap_door)
@app.route("/refresh")
def refresh():
    global USER_LST
    mode = request.args.get("mode")
    if mode == "users":
        USER_LST = read_file(USERFILE)
        return f"刷新用户列表成功<p>{USER_LST}"
    elif mode == "files":
        init_file_sending()
        return f"刷新文件列表成功<p>{'<p>'.join(list(map(str,FILE_LIST)))}"
    return redirect('/')
########################################
if __name__ =="__main__":
    init_file()
    init_file_sending()
    app.run(host=IP, port=PORT, debug=True)
