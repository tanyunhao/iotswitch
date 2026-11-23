# -*- coding: utf-8 -*-
"""
物联网开关模拟器
================
模拟真实设备的行为，配合 uni-app 开关页面联调：
  1. 连接 MQTT Broker
  2. 订阅每个开关的控制主题  iot/<设备ID>/switch/set
  3. 收到 {"switch": 1|0} 指令后，模拟执行延迟，再向状态主题
     iot/<设备ID>/switch/state 回传 {"switch": 1|0}
  4. 上线时主动上报一次当前状态（默认全关）

依赖安装：
  pip install paho-mqtt

用法示例：
  # 默认：连接 EMQX 公共服务器，模拟 switch-001 和 switch-002 两个开关
  python switch_simulator.py

  # 指定自己的服务器和账号
  python switch_simulator.py --broker 192.168.1.100 --port 1883 --username admin --password 123456

  # 模拟 3 个开关，指令执行延迟 1 秒
  python switch_simulator.py --devices switch-001,switch-002,switch-003 --delay 1

  # 自定义主题前缀（默认 iot）
  python switch_simulator.py --prefix home
"""
import argparse
import json
import random
import signal
import sys
import threading
import time

import paho.mqtt.client as mqtt


def parse_args():
    p = argparse.ArgumentParser(description="物联网开关模拟器（配合 uni-app 开关页面联调）")
    p.add_argument("--broker", default="broker.emqx.io", help="MQTT 服务器地址，默认 broker.emqx.io")
    p.add_argument("--port", type=int, default=1883, help="MQTT TCP 端口，默认 1883（TLS 用 8883）")
    p.add_argument("--username", default=None, help="用户名（可选）")
    p.add_argument("--password", default=None, help="密码（可选）")
    p.add_argument("--devices", default="switch-001,switch-002",
                   help="设备 ID 列表，逗号分隔，默认 switch-001,switch-002")
    p.add_argument("--prefix", default="iot", help="主题前缀，默认 iot")
    p.add_argument("--delay", type=float, default=0.3,
                   help="模拟开关动作延迟（秒），默认 0.3，设为 0 表示立即回传")
    p.add_argument("--fail-rate", type=float, default=0.0,
                   help="模拟设备无响应的概率 0~1，默认 0（用于测试 App 的超时提示）")
    args = p.parse_args()
    if not 0 <= args.fail_rate <= 1:
        p.error("--fail-rate 必须在 0~1 之间")
    if args.delay < 0:
        p.error("--delay 不能为负数")
    if not [d.strip() for d in args.devices.split(",") if d.strip()]:
        p.error("--devices 至少需要一个设备 ID")
    return args


class SwitchSimulator:
    def __init__(self, args):
        self.args = args
        self.devices = [d.strip() for d in args.devices.split(",") if d.strip()]
        # 每个设备的当前状态：0 关 / 1 开
        self.states = {dev: 0 for dev in self.devices}
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"py-simulator-{random.randint(1000, 9999)}",
        )
        if args.username:
            self.client.username_pw_set(args.username, args.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def set_topic(self, dev):
        return f"{self.args.prefix}/{dev}/switch/set"

    def state_topic(self, dev):
        return f"{self.args.prefix}/{dev}/switch/state"

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            print(f"[错误] 连接失败，原因码：{reason_code}")
            return
        print(f"[连接] 已连接 {self.args.broker}:{self.args.port}")
        for dev in self.devices:
            client.subscribe(self.set_topic(dev), qos=0)
            print(f"[订阅] {self.set_topic(dev)}")
            # 上线主动上报当前状态，让 App 立即显示真实开关状态
            self.publish_state(dev)

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"[断开] 与服务器断开（原因码 {reason_code}），paho 会自动重连…")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"[警告] 收到无法解析的消息：{msg.topic} -> {msg.payload!r}")
            return

        # 根据主题反查设备 ID：iot/<dev>/switch/set
        parts = msg.topic.split("/")
        if len(parts) != 4 or parts[0] != self.args.prefix or parts[2:] != ["switch", "set"]:
            return
        dev = parts[1]
        if dev not in self.states:
            return

        # 状态查询指令 {"query":1}：只回传当前状态，不改变开关
        if isinstance(payload, dict) and payload.get("query"):
            print(f"[查询] {dev} <- {payload}")
            self.publish_state(dev)
            return

        value = payload.get("switch") if isinstance(payload, dict) else payload
        target = 1 if value in (1, "1", "on", True) else 0
        print(f"[指令] {dev} <- {payload}")

        # 模拟设备偶发无响应（测试 App 端 5 秒超时提示）
        if self.args.fail_rate > 0 and random.random() < self.args.fail_rate:
            print(f"[模拟] {dev} 故意不响应（fail-rate={self.args.fail_rate}）")
            return

        # 模拟继电器动作延迟后再回传状态
        def execute():
            if self.args.delay > 0:
                time.sleep(self.args.delay)
            self.states[dev] = target
            self.publish_state(dev)
            print(f"[执行] {dev} 已{'开启' if target else '关闭'}")

        threading.Thread(target=execute, daemon=True).start()

    def publish_state(self, dev):
        payload = json.dumps({"switch": self.states[dev]})
        # retain=True：Broker 保留最后一条状态，App 重新订阅时能立即拿到真实开关状态，
        # 避免 App 重连后 UI 一律显示"已关闭"
        self.client.publish(self.state_topic(dev), payload, qos=0, retain=True)
        print(f"[上报] {self.state_topic(dev)} -> {payload}")

    def run(self):
        print(f"[启动] 模拟 {len(self.devices)} 个开关：{', '.join(self.devices)}")
        print(f"[提示] 按 Ctrl+C 退出")
        try:
            self.client.connect(self.args.broker, self.args.port, keepalive=60)
        except OSError as e:
            print(f"[错误] 无法连接服务器：{e}")
            sys.exit(1)
        self.client.loop_forever()


def main():
    # 输出重定向到文件/管道时也能实时看到日志
    sys.stdout.reconfigure(line_buffering=True)
    args = parse_args()
    sim = SwitchSimulator(args)
    # Ctrl+C 优雅退出
    signal.signal(signal.SIGINT, lambda *_: (sim.client.disconnect(), sys.exit(0)))
    sim.run()


if __name__ == "__main__":
    main()