<template>
  <view class="page">
    <!-- MQTT 服务器 -->
    <view class="card">
      <view class="card-title-row">
        <view class="title-bar"></view>
        <text class="card-title">MQTT 服务器</text>
      </view>
      <view class="form-item">
        <text class="label">地址（H5 需 ws:// 或 wss://）</text>
        <input class="input" v-model="settings.broker.url" placeholder="ws://broker.emqx.io:8083/mqtt"
          placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">用户名（可选）</text>
        <input class="input" v-model="settings.broker.username" placeholder="留空表示匿名连接"
          placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">密码（可选）</text>
        <input class="input" v-model="settings.broker.password" password placeholder="留空表示无密码"
          placeholder-class="ph" />
      </view>
    </view>

    <!-- 开关列表 -->
    <view class="card">
      <view class="card-header">
        <view class="card-title-row">
          <view class="title-bar"></view>
          <text class="card-title">开关列表</text>
        </view>
        <view class="add-btn" hover-class="btn-hover" @click="startAdd">＋ 添加开关</view>
      </view>

      <view v-if="settings.switches.length === 0" class="empty">暂无开关，请点击右上角添加</view>

      <view v-for="sw in settings.switches" :key="sw.id" class="sw-item">
        <view class="sw-icon">
          <view class="mini-power">
            <view class="mini-line"></view>
            <view class="mini-ring"></view>
          </view>
        </view>
        <view class="sw-info">
          <text class="sw-name">{{ sw.name }}</text>
          <text class="sw-topic">控制：{{ sw.setTopic }}</text>
          <text class="sw-topic">状态：{{ sw.stateTopic }}</text>
        </view>
        <view class="sw-ops">
          <text class="op edit" @click="startEdit(sw)">编辑</text>
          <text class="op del" @click="removeSwitch(sw)">删除</text>
        </view>
      </view>
    </view>

    <!-- 编辑/新增表单 -->
    <view v-if="editing" class="card">
      <view class="card-title-row">
        <view class="title-bar amber"></view>
        <text class="card-title">{{ editing.id ? '编辑开关' : '添加开关' }}</text>
      </view>
      <view class="form-item">
        <text class="label">名称</text>
        <input class="input" v-model="editing.name" placeholder="如：客厅灯" placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">控制主题（App → 设备）</text>
        <input class="input" v-model="editing.setTopic" placeholder="如：iot/light-01/set" placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">状态主题（设备 → App）</text>
        <input class="input" v-model="editing.stateTopic" placeholder="如：iot/light-01/state" placeholder-class="ph" />
      </view>
      <view class="form-actions">
        <view class="pill-btn" hover-class="btn-hover" @click="editing = null">取消</view>
        <view class="pill-btn primary" hover-class="btn-hover" @click="confirmEdit">确定</view>
      </view>
    </view>

    <view class="save-btn" hover-class="save-hover" @click="save">保存并应用</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { loadSettings, saveSettings, newSwitchId } from '@/utils/settings'

const settings = ref(loadSettings())
const editing = ref(null) // 正在编辑的开关副本，null 表示表单关闭

function startAdd() {
  editing.value = { id: '', name: '', setTopic: '', stateTopic: '' }
}

function startEdit(sw) {
  editing.value = { ...sw }
}

function confirmEdit() {
  const e = editing.value
  if (!e.name.trim()) return uni.showToast({ title: '请填写名称', icon: 'none' })
  if (!e.setTopic.trim() || !e.stateTopic.trim()) {
    return uni.showToast({ title: '请填写控制主题和状态主题', icon: 'none' })
  }
  e.name = e.name.trim()
  e.setTopic = e.setTopic.trim()
  e.stateTopic = e.stateTopic.trim()

  // 不同开关不能共用主题，否则一条状态消息会同时驱动多个开关
  const dup = settings.value.switches.find(
    (s) => s.id !== e.id && (s.setTopic === e.setTopic || s.stateTopic === e.stateTopic)
  )
  if (dup) {
    return uni.showToast({ title: `主题与「${dup.name}」重复，请修改`, icon: 'none' })
  }

  if (e.id) {
    const idx = settings.value.switches.findIndex((s) => s.id === e.id)
    if (idx >= 0) settings.value.switches.splice(idx, 1, e)
  } else {
    e.id = newSwitchId()
    settings.value.switches.push(e)
  }
  editing.value = null
}

function removeSwitch(sw) {
  uni.showModal({
    title: '删除开关',
    content: `确定删除「${sw.name}」吗？`,
    success: (res) => {
      if (res.confirm) {
        settings.value.switches = settings.value.switches.filter((s) => s.id !== sw.id)
        if (editing.value && editing.value.id === sw.id) editing.value = null
      }
    },
  })
}

function save() {
  const url = settings.value.broker.url.trim()
  if (!/^wss?:\/\/.+/.test(url)) {
    return uni.showToast({ title: '服务器地址需以 ws:// 或 wss:// 开头', icon: 'none' })
  }
  if (settings.value.switches.length === 0) {
    return uni.showToast({ title: '请至少保留一个开关', icon: 'none' })
  }
  settings.value.broker.url = url
  saveSettings(JSON.parse(JSON.stringify(settings.value)))
  uni.showToast({ title: '已保存', icon: 'success' })
  setTimeout(() => {
    // 直接通过 URL 进入设置页时没有上一页，回退到开关页
    uni.navigateBack({
      fail: () => uni.redirectTo({ url: '/pages/switch/switch' }),
    })
  }, 600)
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  background: radial-gradient(ellipse 90% 40% at 50% -10%, rgba(52, 211, 153, 0.08), transparent),
    #0f1420;
  box-sizing: border-box;
}
.card {
  background: linear-gradient(145deg, #1c2536, #161e2e);
  border: 1rpx solid #232e45;
  border-radius: 28rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.3);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}
.title-bar {
  width: 8rpx;
  height: 30rpx;
  border-radius: 6rpx;
  background: linear-gradient(180deg, #34d399, #0ea5e9);
}
.title-bar.amber {
  background: linear-gradient(180deg, #fbbf24, #f59e0b);
}
.card-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #f2f6fc;
}
.add-btn {
  font-size: 26rpx;
  color: #34d399;
  padding: 8rpx 4rpx;
}
.btn-hover { opacity: 0.6; }

.form-item { margin-top: 26rpx; }
.label {
  display: block;
  font-size: 24rpx;
  color: #8b96ab;
  margin-bottom: 12rpx;
}
.input {
  background: #0f1420;
  border: 1rpx solid #2a3550;
  border-radius: 16rpx;
  padding: 20rpx 24rpx;
  font-size: 26rpx;
  color: #e8edf5;
}
.ph { color: #55617a; }

.empty {
  font-size: 24rpx;
  color: #55617a;
  text-align: center;
  padding: 30rpx 0 10rpx;
}
.sw-item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid rgba(42, 53, 80, 0.5);
}
.sw-item:last-child { border-bottom: none; }
.sw-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 20rpx;
  background: rgba(52, 211, 153, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mini-power {
  position: relative;
  width: 36rpx;
  height: 36rpx;
}
.mini-ring {
  position: absolute;
  inset: 0;
  border: 4rpx solid #34d399;
  border-top-color: transparent;
  border-radius: 50%;
  transform: rotate(-90deg);
}
.mini-line {
  position: absolute;
  left: 50%;
  top: -3rpx;
  width: 4rpx;
  height: 18rpx;
  margin-left: -2rpx;
  background: #34d399;
  border-radius: 4rpx;
  z-index: 1;
}
.sw-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: 22rpx;
}
.sw-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #f2f6fc;
}
.sw-topic {
  font-size: 20rpx;
  color: #55617a;
  margin-top: 4rpx;
  word-break: break-all;
  font-family: 'Consolas', 'Menlo', monospace;
}
.sw-ops {
  display: flex;
  gap: 24rpx;
  margin-left: 20rpx;
  flex-shrink: 0;
}
.op { font-size: 26rpx; }
.op.edit { color: #93c5fd; }
.op.del { color: #f87171; }

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 20rpx;
  margin-top: 32rpx;
}
.pill-btn {
  padding: 12rpx 48rpx;
  border-radius: 100rpx;
  font-size: 26rpx;
  color: #c6cede;
  background: rgba(139, 150, 171, 0.12);
  border: 1rpx solid #2a3550;
}
.pill-btn.primary {
  color: #0f1420;
  font-weight: 600;
  background: linear-gradient(135deg, #34d399, #10b981);
  border: none;
}

.save-btn {
  margin-top: 12rpx;
  padding: 26rpx 0;
  border-radius: 100rpx;
  text-align: center;
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  color: #0f1420;
  background: linear-gradient(135deg, #34d399, #0ea5e9);
  box-shadow: 0 12rpx 40rpx rgba(52, 211, 153, 0.3);
  transition: transform 0.2s;
}
.save-hover { transform: scale(0.98); opacity: 0.9; }
</style>