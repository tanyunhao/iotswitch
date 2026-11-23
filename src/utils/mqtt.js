/**
 * MQTT 通信模块封装（单例）
 *
 * 说明：mqtt.js 依赖标准 WebSocket，适用于 H5 / App(webview) 端。
 * 微信小程序端原生不支持 mqtt.js，需改用 uni.connectSocket + 适配层或原生 MQTT 库。
 *
 * 用法：
 *   import mqttClient from '@/utils/mqtt'
 *   mqttClient.connect()
 *   mqttClient.onStatus(status => { ... })   // 'connecting' | 'connected' | 'reconnecting' | 'offline' | 'error'
 *   mqttClient.onMessage((topic, payload) => { ... })
 *   mqttClient.subscribe('iot/xxx/state')
 *   mqttClient.publish('iot/xxx/set', { switch: 1 })
 *   mqttClient.destroy()
 */
import mqtt from 'mqtt'
import config from '@/config/mqtt'

class MqttClient {
  constructor() {
    this.client = null
    this.status = 'offline'
    this._statusHandlers = new Set()
    this._messageHandlers = new Set()
    // 记录已订阅的 topic，重连成功后自动恢复订阅
    this._subscriptions = new Map() // topic -> qos
  }

  /** 建立连接（幂等，重复调用不会创建多个连接）；url 与 options 由调用方传入（见 settings） */
  connect(url, options = {}) {
    if (this.client) return this.client
    if (!url) throw new Error('MQTT 服务器地址不能为空')

    this._setStatus('connecting')
    const client = mqtt.connect(url, { ...config.options, ...options })
    this.client = client

    // 所有回调先校验身份：destroy 后旧连接的异步事件不得影响新连接的状态
    const isCurrent = () => this.client === client

    client.on('connect', () => {
      if (!isCurrent()) return
      this._setStatus('connected')
      // 恢复订阅
      for (const [topic, qos] of this._subscriptions) {
        client.subscribe(topic, { qos })
      }
    })

    client.on('reconnect', () => {
      if (isCurrent()) this._setStatus('reconnecting')
    })
    client.on('offline', () => {
      if (isCurrent()) this._setStatus('offline')
    })
    client.on('close', () => {
      if (isCurrent() && this.status !== 'reconnecting') this._setStatus('offline')
    })
    client.on('error', (err) => {
      console.error('[MQTT] error:', err)
      if (isCurrent()) this._setStatus('error')
    })

    client.on('message', (topic, message) => {
      if (!isCurrent()) return
      let payload = message.toString()
      try {
        payload = JSON.parse(payload)
      } catch (e) {
        // 非 JSON 消息按原始字符串处理
      }
      this._messageHandlers.forEach((fn) => fn(topic, payload))
    })

    return client
  }

  /** 订阅主题（未连接时也会记录，连接成功后自动订阅） */
  subscribe(topic, qos = 0) {
    this._subscriptions.set(topic, qos)
    if (this.client && this.client.connected) {
      this.client.subscribe(topic, { qos }, (err) => {
        if (err) console.error('[MQTT] subscribe failed:', topic, err)
      })
    }
  }

  unsubscribe(topic) {
    this._subscriptions.delete(topic)
    if (this.client && this.client.connected) {
      this.client.unsubscribe(topic)
    }
  }

  /** 发布消息，payload 为对象时自动序列化为 JSON */
  publish(topic, payload, qos = 0) {
    if (!this.client || !this.client.connected) {
      return Promise.reject(new Error('MQTT 未连接'))
    }
    const data = typeof payload === 'object' ? JSON.stringify(payload) : String(payload)
    return new Promise((resolve, reject) => {
      this.client.publish(topic, data, { qos }, (err) => {
        if (err) reject(err)
        else resolve()
      })
    })
  }

  /** 监听连接状态变化，返回取消函数 */
  onStatus(handler) {
    this._statusHandlers.add(handler)
    handler(this.status) // 立即回调当前状态
    return () => this._statusHandlers.delete(handler)
  }

  /** 监听消息，返回取消函数 */
  onMessage(handler) {
    this._messageHandlers.add(handler)
    return () => this._messageHandlers.delete(handler)
  }

  get connected() {
    return !!(this.client && this.client.connected)
  }

  /** 断开并释放资源（页面卸载时调用） */
  destroy() {
    const client = this.client
    this.client = null // 先置空，使旧连接的异步事件立即失效
    if (client) client.end(true)
    this._subscriptions.clear()
    this._setStatus('offline')
  }

  _setStatus(status) {
    if (this.status === status) return
    this.status = status
    this._statusHandlers.forEach((fn) => fn(status))
  }
}

// 全局单例
const mqttClient = new MqttClient()
export default mqttClient