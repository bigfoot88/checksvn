# -*- coding: utf8 -*-'
import os, sys, os.path
import pysvn
import time

client = pysvn.Client()

def date_list_to_str(date_list):
    date_str1 = ''
    for i in date_list:
        date_str1 += '-' + i
    date_str = date_str1.lstrip('-')
    return date_str

def compare_time(time1, time2):
    '''
    比较时间大小,cc = time1 - time2, 返回cc
    :param time1: # 字符型日期，如'2019-09-10'
    :param time2: # 字符型日期，如'2019-09-20'
    :return:
    '''

    t1 = time.strptime(time1, "%Y-%m-%d")
    t2 = time.strptime(time2, '%Y-%m-%d')
    # 转为整型相减
    s_timestamp = int(time.mktime(t1))
    e_timestamp = int(time.mktime(t2))
    cc = s_timestamp - e_timestamp
    return cc

# 排除相同日志
def rep(str, samestr):
    strs = str.split('\&')
    if len(strs) <= 0:
        return False
    for s in strs:
        if s == samestr:
            return True
    return False

# 排除过滤
def repignore(str):
    str1 = "ignore"
    for i in ignores:
        pos = str.rfind(i)
        if pos >= 0:
            return False
    return True


ignores = {"ignore", "commit", "testcode"}

def writeAppSvnInfo(d):
    cfg = readIni(basedir + "/" + pf + "_apprev.log")

    info = client.info(d + "/main")
    cfg["prev"] = cfg.get("rev") or 0
    cfg["rev"] = info.revision.number
    writeIni(cfg, basedir + "/" + pf + "_apprev.log")


def writeIni(cfg, fn):
    cfgf = open(fn, "w")
    print(cfg)
    for k in cfg:
        cfgf.write(k + "=" + str(cfg[k]) + "\n")
    cfgf.close()


def fmtDateTime(t):
    '''
    :param t: 时间戳，如：1557716103.122426
    :return: 返回字符串时间，如：“2019-05-13 02:55:03”
    '''
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def getsvnLog(svn_path, y, m, d, ty, tm, td):
    '''
    读取代码仓库日志，并存入列表变量LogList
    :param svn_path: svn代码仓库网址
    :param y:起始年
    :param m:起始月
    :param d:起始日
    :param ty:结束年
    :param tm:结束月
    :param td:结束日
    :return:
    '''
    start_date = time.mktime((int(y), int(m), int(d), 0, 0, 0, 0, 0, 0))
    end_date = time.mktime((int(ty), int(tm), int(td), 0, 0, 0, 0, 0, 0))
    revision_start = pysvn.Revision(pysvn.opt_revision_kind.date, start_date)
    revision_end1 = pysvn.Revision(pysvn.opt_revision_kind.date, end_date)
    LogList = client.log(svn_path, revision_start, revision_end1)
    return LogList


def write_svnLog_txt(LogList):
    '''
    日志按提交人，以TXT格式输出
    :param LogList: 日志列表
    :return:
    '''
    dic = {}
    for LogInfo in LogList:
        LogInfo.message = LogInfo.message.replace("\n", "")
        if LogInfo.message != "":
            if repignore(LogInfo.message):
                if LogInfo.author not in dic:
                    dic[LogInfo.author] = {"msg": "", "name": LogInfo.author, "date": "", "showmsg": ""}
                # else:
                if not rep(dic[LogInfo.author]["msg"], LogInfo.message):
                    dic[LogInfo.author]["msg"] += LogInfo.message + "\&"
                    dic[LogInfo.author]["date"] += fmtDateTime(LogInfo.date)
                    """
                    由于获取某时间段的SVN日志时，即使该时间段内没有日志，SVN总是会返回
                    最近一次日志记录，因此需要排除。排除方法是比对最近一次日志的提交时间与起始日期。
                    """
                    last_log_date_str = fmtDateTime(LogInfo.date)[0:10]
                    if compare_time(last_log_date_str, start_date_str) >= 0:
                        dic[LogInfo.author]["showmsg"] += fmtDateTime(LogInfo.date) + "  " + LogInfo.message + "\n"
    s1 = "代码贡献\n"
    for key, value in dic.items():
        s1 += "\n\n\n\n------------------ " + key + " ---------------------------\n" + value["showmsg"]
    f = open("svnLog_style1.txt", "w")
    f.write(s1)
    f.close()



def write_svnLog_cvs(LogList):
    '''
    日志以cvs格式输出
    :param LogList: 日志列表
    :return:
    '''
    dic = {}
    for LogInfo in LogList:
        LogInfo.message = LogInfo.message.replace("\n", "")
        if LogInfo.message != "":
            if repignore(LogInfo.message):
                # if dic.has_key(LogInfo.author) == False:
                if LogInfo.author not in dic:
                    dic[LogInfo.author] = {"msg": "", "name": LogInfo.author, "date": "", "showmsg": ""}
                # else:
                if not rep(dic[LogInfo.author]["msg"], LogInfo.message):
                    dic[LogInfo.author]["msg"] += LogInfo.message + "\&"
                    dic[LogInfo.author]["date"] += fmtDateTime(LogInfo.date)
                    """
                    由于获取某时间段的SVN日志时，即使该时间段内没有日志，SVN总是会返回
                    最近一次日志记录，因此需要排除。排除方法是比对最近一次日志的提交时间与起始日期。
                    """
                    last_log_date_str = fmtDateTime(LogInfo.date)[0:10]
                    if compare_time(last_log_date_str, start_date_str) >= 0:
                        dic[LogInfo.author]["showmsg"] += fmtDateTime(
                            LogInfo.date) + "," + LogInfo.message + "," + LogInfo.author + "\n"
    s1 = "代码贡献\n"
    for key, value in dic.items():
        s1 += value["showmsg"] + "\n"
    f = open("svnLog_style2.csv", "w")
    f.write(s1)
    f.close()


def readIni(fn):
    if not os.path.exists(fn):
        print("ini file not exists:", fn)
        return {}
    print("read ini :", fn)
    cfgf = open(fn)
    cfg = {}
    for l in cfgf.readlines():
        strs = l.strip().split("=")
        print(l)
        if len(strs) == 2:
            cfg[strs[0]] = strs[1]
    return cfg

def get_login(realm, username, may_save):
    print(realm, username)
    global cfg
    id = realm.split(" ")[1]
    print("id=", id)
    return (True, cfg["SVN_USERNAME"], cfg["SVN_PASSWORD"], True)

if __name__ == '__main__':

    cfg = readIni("svnlogConfig.txt")
    client.callback_get_login = get_login
    start_date = cfg["SVN_START_DATE"].split(',')
    end_date = cfg["SVN_END_DATE"].split(',')
    svn_path = cfg["SVN_PATH"]
    print(start_date[0])
    print(start_date[1])
    print(start_date[2])

    print(end_date[0])
    print(end_date[1])
    print(end_date[2])

    """
    将start_date、end_date由列表如[2019,9,1]转为字符串如"2019-9-1"
    以便进行日期对比compare_time(time1,time2)
    由于获取某时间段的SVN日志时，即使该时间段内没有日志，SVN总是会返回
    最近一次日志记录，因此需要排除。排除方法是比对最近一次日志的提交时间与起始日期。
    """
    start_date_str = date_list_to_str(start_date)
    end_date_str = date_list_to_str(end_date)

    # svnrepolist.txt是SVN仓库列表。
    # 在SVN服务器上执行svnrepolist.bat，可获得svnrepolist.txt

    filename = 'E:\\PythonProject\\test\SVN_log\\svnrepolist.txt'
    with open(filename) as file_object:
        repo_addr2s = file_object.readlines()  # 文件行（仓库名称）转换为列表存放
    repo_addr = ''
    repo_addr1 = "https://IP/svn/"  # SVN服务器网址
    LogList = []
    print('正在运行中，请稍候...')
    # 读取各代码仓库日志并写入文件
    for repo_addr2 in repo_addr2s:
        repo_addr = repo_addr1 + repo_addr2.rstrip()  # svn仓库完整路径
        svn_path = repo_addr
        LogList1 = getsvnLog(svn_path, start_date[0], start_date[1], start_date[2],
                            end_date[0], end_date[1], end_date[2])
        LogList.extend(LogList1)
    # 日志按提交人，以TXT格式写入
    write_svnLog_txt(LogList)
    # 日志以cvs格式写入
    # write_svnLog_cvs(LogList)


