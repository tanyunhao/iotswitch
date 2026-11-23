<template>
  <view class="page">
    <!-- 连接状态栏 -->
    <view class="status-bar">
      <view class="status-pill" :class="'status-' + status">
        <view class="dot"></view>
        <text class="status-text">{{ statusText }}</text>
      </view>
      <text class="broker">{{ brokerUrl }}</text>
      <view class="settings-btn" hover-class="btn-hover" @click="goSettings">
        <image class="settings-svg" src="/static/settings.svg" mode="aspectFit" />
        <text>设置</text>
      </view>
    </view>

    <!-- 开关卡片列表 -->
    <view v-for="sw in switches" :key="sw.id" class="card device-card" :class="{ active: states[sw.id]?.on }">
      <view class="device-head">
        <view class="device-titles">
          <text class="device-name">{{ sw.name }}</text>
          <text class="device-topic">{{ sw.setTopic }}</text>
        </view>
        <view class="state-badge" :class="{ on: states[sw.id]?.on, pending: states[sw.id]?.pending }">
          {{ states[sw.id]?.pending ? '确认中' : states[sw.id]?.on ? 'ON' : 'OFF' }}
        </view>
      </view>

      <view class="power-wrap">
        <view v-if="states[sw.id]?.pending" class="spinner"></view>
        <view
          class="power-btn"
          :class="{ on: states[sw.id]?.on, disabled: status !== 'connected' || states[sw.id]?.pending }"
          hover-class="power-hover"
          @click="toggle(sw)"
        >
          <svg class="power-svg" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path d="M512 610.271019c-26.46127 0-47.937083-21.475813-47.937083-47.937083l0-511.328881c0-26.46127 21.475813-47.937083 47.937083-47.937083s47.937083 21.475813 47.937083 47.937083l0 511.328881C559.937083 588.795206 538.46127 610.271019 512 610.271019z" />
            <path d="M512 1023.616503c-245.373947 0-444.983959-199.673928-444.983959-445.047875 0-156.019225 79.511641-297.912989 212.648898-379.533862 22.498471-13.869796 52.027714-6.775108 65.89751 15.787279 13.869796 22.562387 6.775108 52.09163-15.787279 65.89751-104.50284 64.107858-166.884963 175.449722-166.884963 297.849073 0 192.515324 156.59447 349.17371 349.109793 349.17371 192.57924 0 349.17371-156.658386 349.17371-349.17371 0-123.166344-62.957368-234.827789-168.355034-298.743899-22.626303-13.678048-29.848823-43.20729-16.10686-65.833593 13.678048-22.690219 43.20729-29.848823 65.833593-16.10686 134.351663 81.429124 214.502466 223.770301 214.502466 380.748268C957.047875 824.006491 757.373947 1023.616503 512 1023.616503z" />
          </svg>
        </view>
      </view>

      <text class="switch-state" :class="{ on: states[sw.id]?.on }">
        {{ states[sw.id]?.pending ? '等待设备确认…' : states[sw.id]?.on ? '已开启' : '已关闭' }}
      </text>
    </view>

    <view v-if="switches.length === 0" class="card empty-card">
      <text class="empty-text">暂无开关，请到「设置」中添加</text>
    </view>

    <!-- 连接操作 -->
    <view class="actions">
      <view class="pill-btn" :class="{ disabled: status === 'connected' }" hover-class="btn-hover" @click="connect">
        连接
      </view>
      <view class="pill-btn danger" :class="{ disabled: status !== 'connected' }" hover-class="btn-hover" @click="disconnect">
        断开
      </view>
    </view>

    <!-- 消息日志 -->
    <view class="card log-card">
      <view class="log-header">
        <text class="log-title">消息日志</text>
        <text class="log-clear" @click="logs = []">清空</text>
      </view>
      <scroll-view class="log-list" scroll-y :scroll-top="scrollTop">
        <view v-if="logs.length === 0" class="log-empty">暂无消息</view>
        <view v-for="(log, i) in logs" :key="i" class="log-item">
          <view class="log-meta">
            <text class="log-time">{{ log.time }}</text>
            <text class="log-dir" :class="log.dir">{{ log.dir === 'out' ? '发送' : '接收' }}</text>
          </view>
          <text class="log-body">{{ log.topic }}：{{ log.body }}</text>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import mqttClient from '@/utils/mqtt'
import { loadSettings } from '@/utils/settings'

const switches = ref([])
const brokerUrl = ref('')
const status = ref('offline')
const states = ref({}) // { [switchId]: { on, pending } }
const logs = ref([])
const scrollTop = ref(0)

const pendingTimers = {} // switchId -> timer
let offStatus = null
let offMessage = null
let brokerOptions = {}

const statusText = computed(() => ({
  connecting: '连接中…',
  connected: '已连接',
  reconnecting: '重连中…',
  offline: '未连接',
  error: '连接错误',
}[status.value] || status.value))

function addLog(dir, topic, payload) {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  logs.value.push({
    time: `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`,
    dir,
    topic,
    body: typeof payload === 'object' ? JSON.stringify(payload) : String(payload),
  })
  if (logs.value.length > 100) logs.value.shift()
  scrollTop.value = 99999
}

function connect() {
  try {
    mqttClient.connect(brokerUrl.value, brokerOptions)
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

function disconnect() {
  mqttClient.destroy()
}

function goSettings() {
  uni.navigateTo({ url: '/pages/settings/settings' })
}

async function toggle(sw) {
  const st = states.value[sw.id]
  if (status.value !== 'connected' || st.pending) return
  const target = !st.on
  const payload = { switch: target ? 1 : 0, ts: Date.now() }

  try {
    await mqttClient.publish(sw.setTopic, payload)
    addLog('out', sw.setTopic, payload)
    // 等待设备通过状态主题确认，超时提示
    st.pending = true
    pendingTimers[sw.id] = setTimeout(() => {
      delete pendingTimers[sw.id]
      st.pending = false
      uni.showToast({ title: `「${sw.name}」未响应，请检查设备是否在线`, icon: 'none' })
    }, 5000)
  } catch (e) {
    uni.showToast({ title: '发送失败：' + e.message, icon: 'none' })
  }
}

function handleState(sw, payload) {
  // 兼容 {"switch":1} / {"switch":"on"} / 纯数字或字符串
  const v = typeof payload === 'object' ? payload.switch : payload
  const st = states.value[sw.id]
  st.on = v === 1 || v === '1' || v === 'on' || v === true
  if (st.pending) {
    st.pending = false
    clearTimeout(pendingTimers[sw.id])
    delete pendingTimers[sw.id]
  }
}

function clearAllTimers() {
  Object.values(pendingTimers).forEach(clearTimeout)
  Object.keys(pendingTimers).forEach((k) => delete pendingTimers[k])
}

/** 读取设置并（重新）建立连接：首次进入和从设置页返回时都会执行 */
function init() {
  const settings = loadSettings()
  switches.value = settings.switches
  brokerUrl.value = settings.broker.url

  const opts = {}
  if (settings.broker.username) opts.username = settings.broker.username
  if (settings.broker.password) opts.password = settings.broker.password
  brokerOptions = opts

  // 重置状态与连接
  clearAllTimers()
  mqttClient.destroy()
  states.value = {}
  for (const sw of switches.value) {
    states.value[sw.id] = { on: false, pending: false }
    mqttClient.subscribe(sw.stateTopic)
  }
  connect()
}

// 事件监听只注册一次
offStatus = mqttClient.onStatus((s) => {
  status.value = s
  // 连接/重连成功后主动查询各设备当前状态（公共 broker 可能禁用 retain，不能依赖保留消息）
  if (s === 'connected') {
    for (const sw of switches.value) {
      const query = { query: 1 }
      mqttClient.publish(sw.setTopic, query)
        .then(() => addLog('out', sw.setTopic, query))
        .catch(() => {})
    }
  }
})
offMessage = mqttClient.onMessage((topic, payload) => {
  addLog('in', topic, payload)
  const sw = switches.value.find((s) => s.stateTopic === topic)
  if (sw) handleState(sw, payload)
})

onShow(init)

onUnmounted(() => {
  clearAllTimers()
  offStatus && offStatus()
  offMessage && offMessage()
  mqttClient.destroy()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  background: radial-gradient(ellipse 90% 40% at 50% -10%, rgba(52, 211, 153, 0.08), transparent),
    #0f1420;
  box-sizing: border-box;
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx 24rpx;
  border-radius: 20rpx;
  background: rgba(28, 37, 54, 0.8);
  border: 1rpx solid #232e45;
  margin-bottom: 24rpx;
}
.status-pill {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: 8rpx 20rpx;
  border-radius: 100rpx;
  background: rgba(139, 150, 171, 0.12);
  flex-shrink: 0;
}
.dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #8b96ab;
}
.status-text {
  font-size: 24rpx;
  color: #c6cede;
  font-weight: 600;
}
.status-connected { background: rgba(52, 211, 153, 0.12); }
.status-connected .dot {
  background: #34d399;
  box-shadow: 0 0 12rpx rgba(52, 211, 153, 0.8);
}
.status-connected .status-text { color: #34d399; }
.status-connecting, .status-reconnecting { background: rgba(251, 191, 36, 0.12); }
.status-connecting .dot, .status-reconnecting .dot {
  background: #fbbf24;
  animation: blink 1s ease-in-out infinite;
}
.status-connecting .status-text, .status-reconnecting .status-text { color: #fbbf24; }
.status-error { background: rgba(248, 113, 113, 0.12); }
.status-error .dot { background: #f87171; }
.status-error .status-text { color: #f87171; }
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.broker {
  flex: 1;
  font-size: 20rpx;
  color: #55617a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.settings-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 24rpx;
  color: #93c5fd;
  flex-shrink: 0;
  padding: 8rpx 4rpx;
}
.settings-svg {
  width: 32rpx;
  height: 32rpx;
}
.btn-hover { opacity: 0.6; }

/* 卡片 */
.card {
  background: linear-gradient(145deg, #1c2536, #161e2e);
  border: 1rpx solid #232e45;
  border-radius: 28rpx;
  padding: 36rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.3);
}
.device-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: border-color 0.4s, box-shadow 0.4s;
}
.device-card.active {
  border-color: rgba(52, 211, 153, 0.45);
  box-shadow: 0 12rpx 48rpx rgba(52, 211, 153, 0.12);
}
.device-head {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.device-titles {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.device-name {
  font-size: 34rpx;
  font-weight: 700;
  color: #f2f6fc;
}
.device-topic {
  font-size: 20rpx;
  color: #55617a;
  margin-top: 8rpx;
  word-break: break-all;
}
.state-badge {
  padding: 6rpx 20rpx;
  border-radius: 100rpx;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
  color: #8b96ab;
  background: rgba(139, 150, 171, 0.12);
  flex-shrink: 0;
}
.state-badge.on {
  color: #34d399;
  background: rgba(52, 211, 153, 0.14);
}
.state-badge.pending {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.14);
}

/* 电源按钮 */
.power-wrap {
  position: relative;
  margin: 44rpx 0 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.spinner {
  position: absolute;
  width: 252rpx;
  height: 252rpx;
  border-radius: 50%;
  border: 4rpx solid transparent;
  border-top-color: #fbbf24;
  animation: spin 0.9s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.power-btn {
  width: 210rpx;
  height: 210rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #232e45, #1a2233);
  border: 2rpx solid #2a3550;
  box-shadow: inset 0 4rpx 12rpx rgba(255, 255, 255, 0.03), 0 10rpx 30rpx rgba(0, 0, 0, 0.4);
  transition: all 0.35s ease;
}
.power-hover { transform: scale(0.95); }
.power-btn.on {
  background: linear-gradient(135deg, #34d399, #10b981);
  border-color: transparent;
  box-shadow: 0 0 60rpx rgba(52, 211, 153, 0.45), 0 10rpx 30rpx rgba(16, 185, 129, 0.3);
}
.power-btn.disabled { opacity: 0.45; }
.power-svg {
  width: 88rpx;
  height: 88rpx;
}
.power-svg path {
  fill: #55617a;
  transition: fill 0.35s;
}
.power-btn.on .power-svg path {
  fill: #fff;
}

.switch-state {
  font-size: 28rpx;
  color: #8b96ab;
  transition: color 0.3s;
}
.switch-state.on {
  color: #34d399;
  font-weight: 600;
}
.empty-card { padding: 60rpx; align-items: center; }
.empty-text { font-size: 26rpx; color: #55617a; }

/* 连接操作 */
.actions {
  display: flex;
  justify-content: center;
  gap: 24rpx;
  margin-bottom: 24rpx;
}
.pill-btn {
  padding: 14rpx 56rpx;
  border-radius: 100rpx;
  font-size: 26rpx;
  color: #93c5fd;
  background: rgba(147, 197, 253, 0.1);
  border: 1rpx solid rgba(147, 197, 253, 0.25);
}
.pill-btn.danger {
  color: #f87171;
  background: rgba(248, 113, 113, 0.08);
  border-color: rgba(248, 113, 113, 0.25);
}
.pill-btn.disabled { opacity: 0.35; }

/* 日志 */
.log-card { padding: 28rpx; }
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.log-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #c6cede;
}
.log-clear {
  font-size: 24rpx;
  color: #93c5fd;
}
.log-list { height: 320rpx; }
.log-empty {
  font-size: 24rpx;
  color: #55617a;
  text-align: center;
  padding-top: 40rpx;
}
.log-item {
  padding: 12rpx 0;
  border-bottom: 1rpx solid rgba(42, 53, 80, 0.5);
  font-size: 22rpx;
}
.log-meta {
  display: flex;
  align-items: center;
  gap: 14rpx;
}
.log-time {
  color: #55617a;
  font-family: 'Consolas', 'Menlo', monospace;
}
.log-dir {
  padding: 2rpx 14rpx;
  border-radius: 8rpx;
  font-size: 20rpx;
}
.log-dir.out {
  color: #93c5fd;
  background: rgba(147, 197, 253, 0.1);
}
.log-dir.in {
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
}
.log-body {
  display: block;
  margin-top: 6rpx;
  color: #8b96ab;
  word-break: break-all;
  font-family: 'Consolas', 'Menlo', monospace;
}
</style>