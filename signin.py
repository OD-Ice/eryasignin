import base64
import requests
from bs4 import BeautifulSoup, element
import re
import time
import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import memcache


class SignIn:
    def __init__(self):
        self.login_url = 'https://passport2.chaoxing.com/fanyalogin'
        self.username = 'phone_number'  # 修改为自己的账号
        self.password = 'password'  # 修改为自己的密码
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36 Edg/86.0.622.43'
        self.headers = {'User-Agent': self.user_agent}
        # 查询字符串修改为自己的，就是后面的courseId和jclassId
        self.task_list_url = 'https://mobilelearn.chaoxing.com/widget/pcpick/stu/index?courseId=000000000&jclassId=00000000'

        # 邮件相关
        self.mail_pass = 'inputyours'  # 邮箱口令
        self.from_addr = 'sender@haha.com'  # 发送账号
        self.to_addr = 'receiver@hehe.com'  # 接收账号
        self.smtp_port = 465  # 固定端口
        self.smtp_server = 'smtp.qq.com'  # 固定写死，以qq邮箱为例，其他邮箱发送方法请自行百度

    def login(self):
        # 实现登录
        pwd = base64.b64encode(self.password.encode())
        data = {
            'fid': -1,
            'uname': self.username,
            'password': pwd,
            'refer': 'http://i.chaoxing.com',
            't': 'true'
        }
        r = requests.Session()
        r.post(self.login_url, data=data, headers=self.headers)

        response = r.get(self.task_list_url, headers=self.headers)
        self.cookie = requests.utils.dict_from_cookiejar(r.cookies)
        self.uid =self.cookie['UID']
        html = response.content.decode()
        return html

    def parse(self):
        mc = memcache.Client('127.0.0.1:11211', debug=False)  # 连接memcached
        url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax"  # 签到信息提交的网址，这个别动
        html = self.login()
        soup = BeautifulSoup(html, 'lxml')
        div = soup.find('div', id='startList')
        for content in div.contents:
            if isinstance(content, element.Tag):
                mct_nod = content.find('div', 'Mct')
                onclick = mct_nod.attrs['onclick']
                activeId = re.search(r'activeDetail\((.*?),', onclick).group(1)
                activeType = int(re.search(r',(.*?),', onclick).group(1))
                memcache_activeId = mc.get(activeId)  # 判断缓存中是否已经完成任务
                if activeType == 2 and not memcache_activeId:
                    data = {
                        'name': '',  # 感觉没啥用？好像是显示的签到者名字，不太清楚
                        'address': '阿斯加德',  # 修改成需要显示的地址
                        'activeId': activeId,
                        'uid': self.uid,
                        'longitude': 52.1314,  # 经度
                        'latitude': 41.3125,  # 纬度
                    }
                    res = requests.post(url, data=data, headers=self.headers, cookies=self.cookie)
                    print(f'签到结果：{res.text}')
                    if res.text == 'success':
                        self.email('签到成功！你男朋友真厉害！')  # 签到成功发送的消息
                        mc.set(activeId, activeId, time=60*30)  # 将签到成功的任务加入缓存
                    else:
                        self.email('签到失败！快联系你对象改bug了！')  # 签到失败发送的消息

    def email(self, message):
        # 配置服务器，不需要修改
        stmp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        stmp.login(self.from_addr, self.mail_pass)

        # 组装发送内容
        message = MIMEText(message, 'plain', 'utf-8')
        message['From'] = Header("亲爱的男朋友~", 'utf-8')  # 发件人
        message['To'] = Header("可爱的女朋友~", 'utf-8')  # 收件人
        subject = '叮咚~签到提醒~'  # 邮件标题
        message['Subject'] = Header(subject, 'utf-8')

        try:
            stmp.sendmail(self.from_addr, self.to_addr, message.as_string())
        except Exception as e:
            print('邮件发送失败--！' + str(e))
        print('邮件发送成功^_^')


if __name__ == '__main__':
    sign_in = SignIn()
    sign_in.email('自动签到监听程序启动...')
    while True:
        sign_in.parse()
        print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} 处理完成！')
        time.sleep(3*60)  # 三分钟检测一次，不建议速度过快
