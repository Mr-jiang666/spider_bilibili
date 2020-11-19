import re
import time

import requests
import threading
import json
from queue import Queue
from Handle_mongo import mongo


# 定义一个请求方法用于反复调用
def handle_request(url,cookie=None):
    # IP代理，这里使用的是阿布云代理
    proxy = {
        "http": "http://H2K9D2VE55R3R11D:109D54050BD2A0A1@http-dyn.abuyun.com:9020",
        "https": "http://H2K9D2VE55R3R11D:109D54050BD2A0A1@http-dyn.abuyun.com:9020",
    }
    # 如果没有传递cookie，则请求时不携带cookie
    if  cookie == None:
        # 不加cookie的头部字段
        header = {
            "origin": "https://www.bilibili.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36",
        }
        # 添加代理后可能会请求失败，使用循环加try进行重试
        while True:
            try:
                res = requests.get(url=url, headers=header, timeout=5)  # ,proxies = proxy
                res.encoding = 'utf-8'
                break
            except:
                continue
    # 如果函数传递有cookie信息，则使用带有cookie字段的头部进行请求
    else:
        # 带有cookie的头部字段
        header = {
            "origin": "https://www.bilibili.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36",
            "cookie" : cookie
        }
        # 添加代理后可能会请求失败，使用循环加try进行重试
        while True:
            try:
                res = requests.get(url=url, headers=header, timeout=5)  # ,proxies = proxy
                res.encoding = 'utf-8'
                break
            except:
                continue
    # 返回res.text
    return res.text


# 日志文件输出方法
def write_log(log_text):
    with open("bilibili_log.txt","a+",encoding="utf-8") as f:
        f.write(log_text)
        f.write("\n")


# 定义获取所有频道信息的线程类
class bilibili_pindao_get(threading.Thread):
    # 重写父类，定义公共变量和传入的参数
    def __init__(self,thread_name_pindao,pindao_queue,lock):
        super(bilibili_pindao_get,self).__init__()
        self.thread_name_pindao =thread_name_pindao
        self.pindao_queue = pindao_queue
        self.lock = lock

    # 线程类的run方法，主逻辑编写的地方
    def run(self):
        # 输出线程信息
        print("当前启动的网页处理线程为：{thread_name}".format(thread_name = self.thread_name_pindao))
        # 拼接频道信息接口url
        num = 0
        while num < 2545:
            pingdao_url = "https://api.bilibili.com/x/web-interface/web/channel/category/channel_arc/list?id=0&offset={0}".format(num)
            # 将请求后返回的response.text格式化为json格式
            res = json.loads(handle_request(pingdao_url))
            # 提取信息
            for item in res['data']['archive_channels']:
                # 定义字段装载数据
                info = {}
                # 频道ID
                info['pindao_id'] = item['id']
                # 向队列中传递pindao_id
                self.pindao_queue.put(info['pindao_id'], block=False)
                # 频道名称
                info['name'] = item['name']
                # 频道订阅数
                try:
                    info['subscribed_count'] = item['subscribed_count']
                except:
                    info['subscribed_count'] = 0
                # 频道视频量
                info['archive_count'] = item['archive_count']
                # 频道精选视频数
                try:
                    info['featured_count'] = item['featured_count']
                except:
                    info['featured_count'] = 0
                # 调用线程锁
                with self.lock:
                    # 将获取到的频道信息存储到mangoDB数据库中
                    mongo.insert_data("bilibili_pindao", info)
            num += 6

# 定义获取bvid的线程类
class bilibili_bvid_get(threading.Thread):
    # 重写父类，定义公共变量和传入的参数
    def __init__(self,thread_name_bvid,pindao_queue,bvid_queue):
        super(bilibili_bvid_get,self).__init__()
        self.thread_name_bvid = thread_name_bvid
        self.pindao_queue = pindao_queue
        self.bvid_queue = bvid_queue

    # 解析方法，获取bvid并用列表方式向bvid_queue里传递bvid和频道ID
    def parse(self,pindao_id):
        # 初始offset值，拼接bvid接口url需要用到
        offset = ""
        # 使用循环进行不断地拼接、请求、解析、传递等重复操作
        while True:
            bvid_url = "https://api.bilibili.com/x/web-interface/web/channel/multiple/list?channel_id={0}&sort_type=new&offset={1}&page_size=30".format(
                pindao_id,offset)
            res = handle_request(bvid_url)
            result = json.loads(res)
            # 改变offset的值，用以下一个循环中拼接url
            offset = result['data']['offset']
            for item in result['data']['list']:
                # 向bvid_queue队列中放入bvid与对应的频道ID
                self.bvid_queue.put([item['bvid'],pindao_id],block= False)
            # 结束循环的逻辑
            if offset != "":
                continue
            else:
                break

    # 线程类的run方法，编写主逻辑
    # 此线程类不存储数据，只为了获取bvid
    def run(self):
        # 当队列不为空时运行循环
        while not pindao_flag:
            # 输出线程信息
            print("当前启动的网页处理线程为：{thread_name}".format(thread_name = self.thread_name_bvid))
            # 取出pindao_id，并调用解析方法，可能会失败，要使用try、except
            try:
                pindao_id = self.pindao_queue.get(block=False)
                self.parse(pindao_id)
            except:
                continue


# 定义获取视频信息的线程类
class bilibili_video_info(threading.Thread):
    # 重写父类，定义公共变量和传入的参数
    def __init__(self,thread_name_video,bvid_queue,lock,author_queue):#,author_queue
        super(bilibili_video_info,self).__init__()
        self.thread_name_video = thread_name_video
        self.author_queue = author_queue
        self.lock = lock
        self.bvid_queue = bvid_queue

    # 解析方法，获取author_id并向author_queue里传递author_id
    def parse(self,bvid):
        # 凭借视频播放页url
        url = "https://www.bilibili.com/video/{0}".format(bvid[0])
        # 提取视频播放页中的数据
        while True:
            try:
                res = handle_request(url)
                text = re.compile(r'<script>window.__INITIAL_STATE__=(.*?);\(function')
                result = re.search(text, res).group(1)
                data = json.loads(result)
                break
            except:
                continue
        info = {}
        # aid
        info['aid'] = data['aid']
        # bvid
        info['bvid'] = data['bvid']
        # 频道ID
        info['pindao_id'] = bvid[1]
        # 标题
        info['title'] = data['videoData']['title']
        # 描述信息
        info['desc'] = data['videoData']['desc']
        # 标签
        info['tag'] = []
        for i in data['tags']:
            info['tag'].append(i['tag_name'])
        # 发布者ID
        info['author_id'] = data['videoData']['owner']['mid']
        self.author_queue.put(info['author_id'],block= False)
        # 发布者名称
        info['author_name'] = data['videoData']['owner']['name']
        # 创建时间
        info['create_time'] = time.strftime("%Y--%m--%d %H:%M:%S", time.localtime(data['videoData']['ctime']))
        # 拼接获取播放量、弹幕数、点赞数、投币数、转发数、收藏数的接口url
        # 由于之前接口失效过，所以对应字段获取采用try、except
        json_url = "https://api.bilibili.com/x/web-interface/archive/stat?aid={0}".format(info['aid'])
        # 请求接口url获得response
        response = handle_request(json_url)
        # 格式化response为json数据
        json_data = json.loads(response)
        # 播放量
        try:
            info['view'] = json_data['data']['view']
        # json_url的接口可能维护或无法访问，访问不了的就先设置为0
        except:
            info['view'] = 0
        # 弹幕量
        try:
            info['danmaku'] = json_data['data']['danmaku']
        except:
            info['danmaku'] = 0
        # 点赞数
        try:
            info['like'] = json_data['data']['like']
        except:
            info['like'] = 0
        # 投币数
        try:
            info['coin'] = json_data['data']['coin']
        except:
            info['coin'] = 0
        # 收藏数
        try:
            info['favorite'] = json_data['data']['favorite']
        except:
            info['favorite'] = 0
        # 转发数
        try:
            info['share'] = json_data['data']['share']
        except:
            info['share'] = 0
        # 评论数
        info['reply'] = data['videoData']['stat']['reply']
        # 网页地址
        info['play_url'] = url
        # 返回info字典
        return  info

    # 线程类的run方法，先从bvid_queue里获取pindao_id和bvid,再调用解析方法，并存储解析得来的数据
    def run(self):
        while not bvid_flag:
            print("当前启动的网页处理线程为：{thread_name}".format(thread_name=self.thread_name_video))
            try:
                bvid = self.bvid_queue.get(block=False)
                data = self.parse(bvid)
                with self.lock:
                    mongo.insert_data("bilibili_video",data)
            except:
                continue


# 定义获取用户信息的线程类
class bilibili_author_info(threading.Thread):
    # 定义类里面的公共变量
    def __init__(self,author_thread_name,author_queue,lock):
        super(bilibili_author_info, self).__init__()
        self.author_thread_name = author_thread_name
        self.author_queue = author_queue
        self.lock = lock

    # 解析方法，获取用户信息
    def parse(self,author_id):
        url = "https://api.bilibili.com/x/space/acc/info?mid={0}&jsonp=jsonp".format(author_id)
        url1 = "https://api.bilibili.com/x/relation/stat?vmid={0}&jsonp=jsonp".format(author_id)
        url2 = "https://api.bilibili.com/x/space/upstat?mid={0}&jsonp=jsonp".format(author_id)
        res = handle_request(url)
        data = json.loads(res)
        res1 = handle_request(url1)
        data1 = json.loads(res1)
        cookie = "_uuid=C4B75B76-9DB4-5917-861E-97EE22CAF9B325750infoc; buvid3=F73EFDD4-23F4-422A-A553-C3E1714F8B3053918infoc; rpdid=|(umR~lJ~u~R0J'ulmuY)RYY); _ga=GA1.2.734496038.1596227849; CURRENT_QUALITY=64; LIVE_BUVID=AUTO2215983999543582; blackside_state=1; sid=kgh0qk3q; DedeUserID=412963514; DedeUserID__ckMd5=036a92e6cf17efd1; SESSDATA=43e243ab%2C1615501761%2C347e6*91; bili_jct=26aaa4dc1e55b664c7b5bf3c25613108; CURRENT_FNVAL=80; PVID=6"
        res2 = handle_request(url2,cookie)
        data2 = json.loads(res2)
        info = {}
        # 发布者ID
        info['author_id'] = data['data']['mid']
        # 名字
        info['author_name'] = data['data']['name']
        # 性别
        info['sex'] = data['data']['sex']
        # 生日（不一定有）
        info['birthday'] = data['data']['birthday']
        # bilibili个人认证信息（不一定有）
        info['sign'] = data['data']['sign']
        # 认证说明
        info['sign_title'] = data['data']['official']['title']
        # bilibili个人空间地址
        info['author_url'] = "https://space.bilibili.com/{0}".format(info['author_id'])
        # 总关注数
        info['following'] = data1['data']['following']
        # 总粉丝数
        info['follower'] = data1['data']['follower']
        # 总获赞数
        info['likes'] = data2['data']['likes']
        # 总播放数
        info['play'] = data2['data']['archive']['view']
        return info

    # 线程类的run方法，先从author_queue里获取author_id,再调用解析方法，并存储解析得来的数据
    def run(self):
        while not author_flag:
            print("当前启动的网页处理线程为：{thread_name}".format(thread_name=self.author_thread_name))
            try:
                author_id = self.author_queue.get(block=False)
                data = self.parse(author_id)
                with self.lock:
                    mongo.insert_data("bilibili_author",data)
            except:
                continue


# 设置标志位，当对应的队列取空时改变标志位，结束循环，并结束线程
pindao_flag = False
bvid_flag = False
author_flag = False


def main():
    # 往日志文件输入当前时间，记录此次程序运行
    write_log("本次爬虫启动时间：{time}".format(time=time.time()))
    # 频道队列
    pindao_queue = Queue()
    # bvid队列
    bvid_queue = Queue()
    # 用户队列
    author_queue = Queue()
    # 线程锁
    lock = threading.Lock()
    # 创建获取频道信息的线程池并启动
    pindao_thread_name_list = ["频道信息获取线程一号"]#, "频道信息获取线程二号", "频道信息获取线程三号"
    pindao_thread_list = []
    for pindao_thread_name in pindao_thread_name_list:
        pindao_thread = bilibili_pindao_get(pindao_thread_name, pindao_queue, lock)
        pindao_thread.start()
        pindao_thread_list.append(pindao_thread)
    # 创建获取bvid的线程池并启动
    bvid_thread_name_list = ["bvid获取线程一号","bvid获取线程二号"]#,"bvid获取线程三号"
    bvid_thread_list = []
    for bvid_thread_name in bvid_thread_name_list:
        bvid_thread = bilibili_bvid_get(bvid_thread_name,pindao_queue,bvid_queue)
        bvid_thread.start()
        bvid_thread_list.append(bvid_thread)
    # 创建视频信息获取的线程池并启动
    video_thread_name_list = ["视频信息获取线程一号","视频信息获取线程二号","视频信息获取线程三号"]
    video_thread_list = []
    for video_thread_name in video_thread_name_list:
        video_thread = bilibili_video_info(video_thread_name,bvid_queue,lock,author_queue)#,author_queue
        video_thread.start()
        video_thread_list.append(video_thread)
    # 创建发布者信息获取的线程池并启动
    author_thread_name_list = ["发布者信息获取线程一号","发布者信息获取线程二号","发布者信息获取线程三号"]
    author_thread_list = []
    for author_thread_name in author_thread_name_list:
        author_thread = bilibili_author_info(author_thread_name,author_queue,lock)
        author_thread.start()
        author_thread_list.append(author_thread)
    # 将线程池中的线程挂起，让其自行结束线程
    for pindao_thread_join in pindao_thread_list:
        pindao_thread_join.join()
        print(pindao_thread_join.thread_name_pindao,"处理结束")
    # 判断对应队列是否已经取空，取空后改变标志位，结束线程类中的循环
    global pindao_flag
    while not pindao_queue.empty():
        pass
    pindao_flag = True
    # 将获取bvid线程池中的线程挂起，让其自行结束线程
    for bvid_thread_join in bvid_thread_list:
        bvid_thread_join.join()
        print(bvid_thread_join.thread_name_bvid,"处理结束")
    # 判断对应队列是否已经取空，取空后改变标志位，结束线程类中的循环
    global bvid_flag
    while not bvid_queue.empty():
        pass
    bvid_flag = True
    # 将获取视频信息线程池中的线程挂起，让其自行结束线程
    for video_thread_join in video_thread_list:
        video_thread_join.join()
        print(video_thread_join.thread_name_video,"处理结束")
    # 判断对应队列是否已经取空，取空后改变标志位，结束线程类中的循环
    global author_flag
    while not author_queue.empty():
        pass
    author_flag = True
    # 将获取用户信息线程池中的线程挂起，让其自行结束线程
    for author_thread_join in author_thread_list:
        author_thread_join.join()
        print(author_thread_join.author_thread_name, "处理结束")
    # 往日志文件输入当前时间，记录此次程序运行
    write_log("本次爬虫结束时间：{time}\n".format(time=time.time()))


if __name__ == '__main__':
    main()