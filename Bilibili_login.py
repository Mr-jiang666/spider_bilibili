import time
import json
import requests
import base64
from io import BytesIO
from sys import version_info
from selenium import webdriver
from selenium.webdriver import ActionChains
from PIL import Image

class BILIBILI_login():
    def __init__(self):
        self.username = input("请先输入B站用户名：")
        self.password = input("请先输入B站密码：")
        self.user = input("请先输入图鉴网账号：")
        self.pwd = input("请先输入图鉴网密码：")
        self.browser = webdriver.Chrome()
        self.url = "https://passport.bilibili.com/login"

    def img_zuobiao(self,uname, pwd,  img,keyword):
        img = img.convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        if version_info.major >= 3:
            b64 = str(base64.b64encode(buffered.getvalue()), encoding='utf-8')
        else:
            b64 = str(base64.b64encode(buffered.getvalue()))
        data = {"username": uname, "password": pwd,"typeid": "27","remark":keyword,"image": b64}
        result = json.loads(requests.post("http://api.ttshitu.com/imageXYPlus", json=data).text)
        if result['success']:
            return result["data"]["result"]
        else:
            return result["message"]

    def img_text(self,uname, pwd,  img):
        img = img.convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        if version_info.major >= 3:
            b64 = str(base64.b64encode(buffered.getvalue()), encoding='utf-8')
        else:
            b64 = str(base64.b64encode(buffered.getvalue()))
        data = {"username": uname, "password": pwd,"typeid": "16","image": b64}
        result = json.loads(requests.post("http://api.ttshitu.com/base64", json=data).text)
        if result['success']:
            return result["data"]["result"]
        else:
            return result["message"]

    def crop_image2(self,image_file_name):
        # 截图验证码图片
        # 定位某个元素在浏览器中的位置
        time.sleep(2)
        img = self.browser.find_element_by_xpath("//*[@class='geetest_item_img']")
        location = img.location
        size = img.size
        top, buttom, left, right = location["y"], location["y"] + size["height"], location["x"], location['x'] + size["width"]
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        captcha = screenshot.crop((int(left), int(top), int(right), int(buttom)))
        captcha.save(image_file_name)
        return location

    def crop_image1(self,image_file_name):
        # 截图验证码图片
        # 定位某个元素在浏览器中的位置
        time.sleep(2)
        img = self.browser.find_element_by_xpath("//*[@class='geetest_tip_img']")
        location = img.location
        size = img.size
        top, buttom, left, right = location["y"], location["y"] + size["height"], location["x"], location['x'] + size["width"]
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        captcha = screenshot.crop((int(left), int(top), int(right), int(buttom)))
        captcha.save(image_file_name)
        return location

    def yanzhengma(self):
        # 截取图片
        # 截图是千万注意！！！！屏幕显示比例要设置为100%，否则坐标会有偏差
        self.crop_image1("captcha1.png")
        zuobiao = self.crop_image2("captcha2.png")
        img_path1 = "captcha1.png"
        img1 = Image.open(img_path1)
        result1 = self.img_text(uname=self.user, pwd=self.pwd, img=img1)
        print("验证码字体为："+result1)
        img_path2 = "captcha2.png"
        img2 = Image.open(img_path2)
        result2 = self.img_zuobiao(uname=self.user, pwd=self.pwd, img=img2, keyword=result1)
        print("验证码坐标为："+result2)
        result_move = result2.split("|")
        for result in result_move:
            x = zuobiao['x'] + int(result.split(",")[0])
            y = zuobiao['y'] + int(result.split(",")[1])
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=y).click().perform()
            ActionChains(self.browser).move_by_offset(xoffset=-x, yoffset=-y).perform()
        self.browser.find_element_by_xpath("//div[@class='geetest_commit_tip']").click()

    def login(self):
        print("正在自动登录中...")
        self.browser.get(self.url)
        self.browser.maximize_window() #很重要！！
        username_ele = self.browser.find_element_by_xpath("//input[@id='login-username']")
        password_ele = self.browser.find_element_by_xpath("//input[@id='login-passwd']")
        username_ele.send_keys(self.username)
        password_ele.send_keys(self.password)
        self.browser.find_element_by_xpath("//a[@class='btn btn-login']").click()
        self.yanzhengma()
        time.sleep(3)
        if "校园学习" in self.browser.page_source:
            print("自动登录成功！")
            self.browser.quit()
        else:
            self.login()

if __name__ == "__main__":
    login = BILIBILI_login()
    login.login()