import requests
import sys


class Report:
    """自动完成体温上报。"""

    def __init__(self) -> None:
        """设定固定的参数。"""
        self.cookies = sys.argv[1].split('#')

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.38',
            'cookie': None
        }

        self.check_url = 'https://jzsz.uestc.edu.cn/wxvacation/checkRegisterNew'

        self.unreturned_url = ''  # TODO Not verified yet.
        self.unreturned_data = {
            # TODO Not verified yet.
        }

        self.returned_url = 'https://jzsz.uestc.edu.cn/wxvacation/monitorRegisterForReturned'
        self.returned_data = {
            'healthCondition': '正常',
            'todayMorningTemperature': '36°C~36.5°C',
            'yesterdayEveningTemperature': '36°C~36.5°C',
            'yesterdayMiddayTemperature': '36°C~36.5°C',
            'location': '四川省成都市郫都区银杏大道'
        }

        self.success = 0
        self.done = 0
        self.fail = 0

    def check_status(self) -> int:
        """检查学生的当前状态。
        ---
        当前状态包括<上报状态>与<在校状态>，据此返回不同的状态码，决定当前循环要采取的行动。

        :return: `int` 学生当前的状态码。
        - 0 : 发生错误
        - 1 : 已经上报
        - 2 : 未上报，不在校
        - 3 : 未上报，在校
        """
        # 尝试对查询站点发起请求。
        response = requests.get(self.check_url, headers=self.headers)
        if response.status_code != 200:
            self.fail += 1
            print('失败：你的网络出了一些问题。')
            return 0

        # 解析查询到的字典。
        data: dict = response.json()['data']
        if data == None:
            self.fail += 1
            print(
                '失败：最大的可能是cookie错了。cookie应该形如：JSESSIONID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
            return 0

        # 检查上报次数。
        applied_times: int = data.get('appliedTimes', None)
        # 如果找不到该字段：
        if applied_times == None:
            self.fail += 1
            print('失败：大概率是学校那边的问题。')
            return 0
        # 如果已经上报过了：
        elif applied_times != 0:
            self.done += 1
            print('该同学已经上报过了。')
            return 1
        # 如果还没上报：
        else:
            # 检查在校状态。
            school_status: int = data.get('schoolStatus', None)
            # 如果找不到该字段：
            if school_status == None:
                self.fail += 1
                print('失败：大概率是学校那边的问题。')
                return 0
            # 如果不在校：
            elif school_status == 0:
                return 2
            # 如果在校：
            elif school_status == 1:
                return 3
            else:
                self.fail += 1
                print('失败：未知的在校状态。')
                return 0

    def do_report(self, url, data) -> None:
        """进行上报。
        ---
        根据学生状态选择对应的数据，上传到对应的站点。

        :param url: 站点，在校和不在校两种状态，对应的上报站点不同，
        :param data: 数据，包括体温、地点等。
        """
        # 尝试对上报站点发起请求。
        response = requests.post(
            url, headers=self.headers, data=data)
        if response.status_code != 200:
            self.fail += 1
            print('失败：你的网络出了一些问题。')
            return

        # 解析返回的状态字典。
        report_status: bool = response.json().get('status', None)
        if report_status == None:
            self.fail += 1
            print('失败：大概率是学校那边的问题。')
        elif report_status == False:
            self.fail += 1
            print('失败：数据已上传，但未上报成功，建议手动确认。')
        else:
            self.success += 1
            print('成功。')

    def run(self):
        print('-' * 60)
        # 遍历每位学生。
        for index, cookie in enumerate(self.cookies):
            print(f'正在为第{index+1}位同学上报...', end='')
            # 为这位同学定制请求头。
            self.headers.update({'cookie': cookie})
            status = self.check_status()
            # 如果未上报且不在校：
            if status == 2:
                self.do_report(url=self.unreturned_url,
                               data=self.unreturned_data)
            # 如果未上报且在校：
            elif status == 3:
                self.do_report(url=self.returned_url, data=self.returned_data)
            # 如果出错或已经上报：
            else:
                continue

        print('-' * 60)
        print(
            f'已完成今天的上报，{self.success}人成功，{self.done}人已经上报，{self.fail}人失败。')


if __name__ == '__main__':
    app = Report()
    app.run()