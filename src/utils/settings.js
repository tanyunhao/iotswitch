/**
 * 物联网设置持久化（uni storage）
 * 结构：{ broker: { url, username, password }, switches: [{ id, name, setTopic, stateTopic }] }
 */
import defaultConfig from '@/config/mqtt'

const STORAGE_KEY = 'iot-settings'

export function defaultSettings() {
  return {
    broker: {
      url: defaultConfig.url,
      username: '',
      password: '',
    },
    switches: [
      {
        id: 'sw-1',
        name: '智能开关',
        setTopic: defaultConfig.topics.set,
        stateTopic: defaultConfig.topics.state,
      },
    ],
  }
}

export function loadSettings() {
  try {
    const s = uni.getStorageSync(STORAGE_KEY)
    if (s && s.broker && s.broker.url && Array.isArray(s.switches)) {
      return s
    }
  } catch (e) {
    console.warn('[settings] load failed:', e)
  }
  return defaultSettings()
}

export function saveSettings(settings) {
  uni.setStorageSync(STORAGE_KEY, settings)
}

export function newSwitchId() {
  return 'sw-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
}