/**
 * MQTT 连接配置
 * H5 / App 端均使用 WebSocket 连接（ws:// 或 wss://）
 * 默认使用 EMQX 公共测试服务器的加密端口 8084（wss），
 * 因为安卓 9+ 默认禁止 ws:// 明文连接；正式环境请替换为自己的 Broker
 */
const deviceId = 'switch-001'

export default {
  // Broker 地址（H5/App 必须走 WebSocket，安卓端建议 wss）
  url: 'wss://broker.emqx.io:8084/mqtt',
  options: {
    clientId: `uniapp-${deviceId}-${Math.random().toString(16).slice(2, 10)}`,
    clean: true,
    connectTimeout: 8000,
    reconnectPeriod: 3000, // 自动重连间隔（ms），0 表示不重连
    keepalive: 60,
    // username: '',
    // password: '',
  },
  deviceId,
  topics: {
    // 下发开关指令：App -> 设备
    set: `iot/${deviceId}/switch/set`,
    // 设备状态上报：设备 -> App
    state: `iot/${deviceId}/switch/state`,
  },
}