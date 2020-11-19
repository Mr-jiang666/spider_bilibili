import os
import time
import requests
import re
import json

from lxml import etree
from urllib import parse


class bilibili():
    # 重写父类
    def __init__(self):
        # 设置请求网页时的头部信息
        self.getHtmlHeaders={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3776.400 QQBrowser/10.6.4212.400",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q = 0.9'
        }
        self.options_headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Access-Control-Request-Headers": "range",
            "Access-Control-Request-Method": "GET",
            "Connection": "keep-alive",
            "Origin": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3776.400 QQBrowser/10.6.4212.400",
        }
        # 设置请求视频资源时的头部信息
        self.downloadVideoHeaders={
            "accept":"*/*",
            "accept-encoding":"gzip, deflate, br",
            "accept-language":"zh-CN,zh;q=0.9",
            "origin":"https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3776.400 QQBrowser/10.6.4212.400",
        }
        self.domain = "https://www.bilibili.com/video/"
        self.session = requests.session()

    # url拼接得到所有需要的url，装在list中返回
    def run(self,fanhao):
        url = parse.urljoin(self.domain,fanhao)
        json_url ='https://api.bilibili.com/x/player/pagelist?bvid='+fanhao+'&jsonp=jsonp'
        try:
            res = self.session.get(url = json_url,headers=self.getHtmlHeaders)
            info_list = json.loads(res.text)['data']
            for item in info_list:
                if len(item) > 1:
                    name = str(item['page']) +'--'+ item['part']
                else:
                    name = item['part']
                num = item['page']
                play_url = url + '?p={num}'.format(num=num)
                try:
                    response = self.session.get(url=play_url, headers=self.getHtmlHeaders)
                    if response.status_code == 200:
                        response = response.text
                        self.parseHtml(response,name,play_url)
                except requests.RequestException:
                    print('ERROR：请求Html错误:')
        except requests.RequestException:
            print("ERROR：该资源可能为av开头或者过于老旧！")

    # 解析页面并提取出得到想要的数据，将得到的数据装在list中返回
    def parseHtml(self,response,name,play_url):
        # 用etree加xpath解析页面和获取标题
        doc = etree.HTML(response)
        title = doc.xpath("//div[@id='viewbox_report']/h1/span/text()")[0]
        # 用正则、json得到视频url
        # 根据页面中的代码书写正则表达式
        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
        # 根据正则表达式在页面中提取对应字典，实践证明获取的两个结果相同，取第一个结果即可
        result = re.findall(pattern, response)[0]
        # 将获取的字典转化为json格式
        temp = json.loads(result)
        try:
            #字段为['data']['dash']['video']则是Bv开头，取baseUrl的值
            dict_video= temp['data']['dash']['video'][0]
            dict_audio= temp['data']['dash']['audio'][0]
            if 'baseUrl' in dict_video.keys() :
                video_url = dict_video['baseUrl']
                self.download_video(name,title,video_url,play_url)
            if 'baseUrl' in dict_audio.keys() :
                audio_url = dict_audio['baseUrl']
                self.download_audio(name,title,audio_url,play_url)
        except:
            print("ERROR：获取音视频url失败！")
        self.CombineVideoAudio(name,title)

    # 定义视频下载的方法
    def download_video(self,name,title,video_url,play_url):
        # 去掉创建文件时的非法字符
        title1 = re.sub(r'[\/:*?"<>|]', '-', title)
        title = title1.replace(" ", "").replace("!","")
        #拼接文件名
        name1 = re.sub(r'[\/:*?"<>|]', '-', name)
        name = name1.replace("&", "and").replace(" ", "").replace("!","")
        filename = name + '.mp4'
        #视频请求下载地址
        self.session.options(url=video_url, stream=True, headers=self.options_headers)
        self.downloadVideoHeaders['referer'] = play_url
        r = self.session.get(url=video_url, stream=True, headers=self.downloadVideoHeaders)
        #根据请求页面的response headers得到content-length，也就是文件的总bit大小
        length = float(r.headers['content-length'])
        count = 0
        count_tmp = 0
        time1 = time.time()
        start_time = time.time()
        path = r'E:\bilibili_video\{dir_title}'.format(dir_title=title)
        # 看是否有该文件夹，没有则创建文件夹
        if not os.path.exists(path):
            os.mkdir(path)
        filepath = path + '\\' + filename  # 设置图片name，注：必须加上扩展名
        if not os.path.exists(filepath):  # 判断文件是否已经存在，避免重复下载
            print('[Start download]:{filename},[File size]:{size:.2f} MB'.format(filename=filename,size=length / 1024 / 1024))  # 开始下载，显示下载文件大小
            with open(filepath, 'wb') as f:  # 显示进度条
                for chunk in r.iter_content(chunk_size=512):
                    if chunk:
                        f.write(chunk)
                        count += len(chunk)
                        if time.time() - time1 > 2:
                            speed = (count - count_tmp) / 1024 / 1024 / 2
                            count_tmp = count
                            print('\r' + '[下载进度]:%s%.2f%%' % ('>' * int(count * 50 / length), float(count / length * 100)),end=' ' + ' Speed:%.2f ' % speed + 'M/S')
                            time1 = time.time()
                end_time = time.time()  # 下载结束时间
                print('\nDownload completed!,times: %.2f秒\n' % (end_time - start_time))  # 输出下载用时时间
            f.close()

    # 定义音频下载的方法
    def download_audio(self, name,title,audio_url,play_url):
        # 去掉创建文件时的非法字符
        title1 = re.sub(r'[\/:*?"<>|]', '-', title)
        title = title1.replace(" ","").replace("!","")
        # 拼接文件名
        name1 = re.sub(r'[\/:*?"<>|]', '-', name)
        name = name1.replace("&","and").replace(" ", "").replace("!","")
        filename = name + '.mp3'
        # 视频请求下载地址
        self.session.options(url=audio_url, stream=True, headers=self.options_headers)
        self.downloadVideoHeaders['referer'] = play_url
        r = self.session.get(url=audio_url, stream=True, headers=self.downloadVideoHeaders)
        # 根据请求页面的response headers得到content-length，也就是文件的总bit大小
        length = float(r.headers['content-length'])
        count = 0
        count_tmp = 0
        time1 = time.time()
        start_time = time.time()
        path = r'E:\bilibili_video\{dir_title}'.format(dir_title=title)
        # 看是否有该文件夹，没有则创建文件夹
        if not os.path.exists(path):
            os.mkdir(path)
        filepath = path + '\\' + filename  # 设置图片name，注：必须加上扩展名
        if not os.path.exists(filepath):
            print('[Start download]:{filename},[File size]:{size:.2f} MB'.format(filename=filename,size=length / 1024 / 1024))  # 开始下载，显示下载文件大小
            with open(filepath, 'wb') as f:  # 显示进度条
                for chunk in r.iter_content(chunk_size=512):
                    if chunk:
                        f.write(chunk)
                        count += len(chunk)
                        if time.time() - time1 > 2:
                            speed = (count - count_tmp) / 1024 / 1024 / 2
                            count_tmp = count
                            print('\r' + '[下载进度]:%s%.2f%%' % ('>' * int(count * 50 / length), float(count / length * 100)),end=' ' + ' Speed:%.2f ' % speed + 'M/S')
                            time1 = time.time()
                end_time = time.time()  # 下载结束时间
                print('\nDownload completed!,times: %.2f秒\n' % (end_time - start_time))  # 输出下载用时时间
            f.close()

    # 音视频合并
    def CombineVideoAudio(self, name, title):
        title1 = re.sub(r'[\/:*?"<>|]', '-', title)
        title = title1.replace(" ", "").replace("!","")
        name1 = re.sub(r'[\/:*?"<>|]', '-', name)
        name = name1.replace("&", "and").replace(" ", "").replace("!","")
        video_filename = name + '.mp4'
        video_filepath = r'E:\bilibili_video\{dir_title}\{video_filename}'.format(dir_title=title,video_filename=video_filename) # 设置图片name，注：必须加上扩展名
        audio_filename = name + '.mp3'
        audio_filepath = r'E:\bilibili_video\{dir_title}\{audio_filename}'.format(dir_title=title,audio_filename=audio_filename)# 设置图片name，注：必须加上扩展名
        out_filename = name + '-.mp4'
        out_filepath = r'E:\bilibili_video\{dir_title}\{out_filename}'.format(dir_title=title,out_filename=out_filename)
        if not os.path.exists(out_filepath):
            cmd = 'ffmpeg -i ' + video_filepath + ' -i ' + audio_filepath + ' -strict -2 -f mp4 ' + out_filepath
            print(cmd)
            # 使用FFmpeg将音视频合并
            # 使用此拼接方法需要安装好FFmpeg并配置好系统path变量，最好在cmd中检查一下命令是否可以运行
            print("开始拼接：{name}".format(name=out_filename))
            try:
                d = os.popen(cmd)
                if "Qavg" not in d.read():
                    # d.read()也就是os.popen(cmd).read()，可以查看命令在cmd中运行后的输出内容
                    print(d.read())
                    print("拼接完成:{name}".format(name=out_filename))
                    os.remove(video_filepath)
                    os.remove(audio_filepath)
            except:
                print("拼接失败:{name}".format(name=out_filename))


if __name__ == '__main__':
    # 替换自己想要下载视频的番号即可，注意要是BV开头的
    fanhao = 'BV1d7411Z7aR'
    bilibili().run(fanhao)

