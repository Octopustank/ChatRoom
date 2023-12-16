'''工具函数和初始化'''

import datetime as dt
import json as js
import os

# 获取工作路径
def init_path():
    global PATH
    path = os.path.abspath(__file__)
    PATH = os.path.dirname(path)
    print(f"[INIT] PATH: {PATH}")
    return PATH

# 当天日志文件和用户文件初始化
def init_file():
    print("[INIT] READ DATA_FILE&USERS")
    PATH = init_path()
    DATA_LST = [];
    DATE_STR = dt.datetime.now().strftime("%y-%m-%d")
    logfiles = os.path.join(PATH,"logfiles")
    LOGFILE = os.path.join(logfiles,f"{DATE_STR}.json")
    bin_ = os.path.join(PATH,"bin")
    USERFILE = os.path.join(bin_,"users.json")
    UIDFILE = os.path.join(bin_,"uid.json")
    UIDB = read_file(UIDFILE)
    USERDB = read_file(USERFILE)
    # 如果当天已存在日志文件，则接着盖楼，否则新建
    if os.path.isfile(LOGFILE):
        DATA_LST = read_file(LOGFILE)
        floor = DATA_LST[-1][1]
        print(f"[INIT] 读取日志:{LOGFILE}")
    else: 
        floor = 1
        print("[INIT] 无已存在日志")
    return [DATA_LST, LOGFILE, UIDB, UIDFILE, USERDB, USERFILE, floor]

# 前7天（最多）历史记录初始化
def init_backlog():
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
    return [BACK_LOG_LST, BACK_LOG_LEN]

#初始化文件传输
def init_file_sending():
    print("[INIT] READ FILE_LIST")
    path = os.path.join(PATH, "cloud")
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
                FILE_LIST.append([file_list[p],"--/-- --:--","-.-.-","server"])
                print(f"[FILE_LIST] ADD: {file_list[p]}")
                flag = True
        if flag: write_file(PATH_FILE_JS, FILE_LIST)#若有文件变动，修正该问题
        
    return [PATH_FILE_JS, PATH_FILES, FILE_LIST]

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
