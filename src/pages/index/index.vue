<template>
  <view class="content">
    <view class="hero">
      <view class="orb">
        <view class="orb-core"></view>
        <view class="orb-ring r1"></view>
        <view class="orb-ring r2"></view>
      </view>
      <text class="app-title">智能家居</text>
      <text class="app-sub">MQTT 物联网设备控制</text>
    </view>

    <view class="entry-card" hover-class="entry-hover" @click="goSwitch">
      <view class="entry-icon">
        <view class="mini-power">
          <view class="mini-line"></view>
          <view class="mini-ring"></view>
        </view>
      </view>
      <view class="entry-text">
        <text class="entry-title">开关控制</text>
        <text class="entry-desc">管理并控制你的物联网开关</text>
      </view>
      <view class="chevron"></view>
    </view>

    <text class="footer">基于 uni-app · MQTT</text>
  </view>
</template>

<script>
export default {
  data() {
    return {
      title: 'Hello',
    }
  },
  onLoad() {},
  methods: {
    goSwitch() {
      uni.navigateTo({ url: '/pages/switch/switch' })
    },
  },
}
</script>

<style scoped>
.content {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 40rpx;
  box-sizing: border-box;
  background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(52, 211, 153, 0.12), transparent),
    #0f1420;
}

/* 顶部光球 */
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 140rpx;
}
.orb {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.orb-core {
  width: 110rpx;
  height: 110rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #34d399, #0ea5e9);
  box-shadow: 0 0 60rpx rgba(52, 211, 153, 0.5);
}
.orb-ring {
  position: absolute;
  border-radius: 50%;
  border: 2rpx solid rgba(52, 211, 153, 0.25);
}
.orb-ring.r1 {
  inset: 10rpx;
  animation: breathe 3s ease-in-out infinite;
}
.orb-ring.r2 {
  inset: -14rpx;
  border-color: rgba(14, 165, 233, 0.15);
  animation: breathe 3s ease-in-out infinite 1.5s;
}
@keyframes breathe {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.08); opacity: 1; }
}
.app-title {
  margin-top: 48rpx;
  font-size: 52rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  color: #f2f6fc;
}
.app-sub {
  margin-top: 14rpx;
  font-size: 26rpx;
  color: #8b96ab;
  letter-spacing: 2rpx;
}

/* 入口卡片 */
.entry-card {
  width: 100%;
  margin-top: 100rpx;
  display: flex;
  align-items: center;
  padding: 36rpx 32rpx;
  border-radius: 28rpx;
  background: linear-gradient(145deg, #1c2536, #161e2e);
  border: 1rpx solid #2a3550;
  box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.35);
  transition: transform 0.2s, border-color 0.2s;
}
.entry-hover {
  transform: scale(0.98);
  border-color: #34d399;
}
.entry-icon {
  width: 92rpx;
  height: 92rpx;
  border-radius: 24rpx;
  background: rgba(52, 211, 153, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mini-power {
  position: relative;
  width: 44rpx;
  height: 44rpx;
}
.mini-ring {
  position: absolute;
  inset: 0;
  border: 5rpx solid #34d399;
  border-top-color: transparent;
  border-radius: 50%;
  transform: rotate(-90deg);
}
.mini-line {
  position: absolute;
  left: 50%;
  top: -4rpx;
  width: 5rpx;
  height: 22rpx;
  margin-left: -2.5rpx;
  background: #34d399;
  border-radius: 4rpx;
  z-index: 1;
}
.entry-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 28rpx;
}
.entry-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #f2f6fc;
}
.entry-desc {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #8b96ab;
}
.chevron {
  width: 18rpx;
  height: 18rpx;
  border-top: 4rpx solid #55617a;
  border-right: 4rpx solid #55617a;
  transform: rotate(45deg);
  flex-shrink: 0;
}

.footer {
  margin-top: auto;
  margin-bottom: 48rpx;
  padding-top: 80rpx;
  font-size: 22rpx;
  color: #55617a;
  letter-spacing: 2rpx;
}
</style>