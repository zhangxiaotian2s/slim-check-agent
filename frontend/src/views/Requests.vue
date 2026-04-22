<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { apiClient } from '@/api/client'

const requests = ref<any[]>([])
const stats = ref<any>(null)
const isLoading = ref(false)
const autoRefresh = ref(true)
const errorMessage = ref('')

let refreshInterval: number | null = null

async function loadStats() {
  try {
    stats.value = await apiClient.getStats()
  } catch (e: any) {
    console.error('Failed to load stats:', e)
  }
}

async function loadRequests() {
  isLoading.value = true
  try {
    requests.value = await apiClient.listRequests()
    errorMessage.value = ''
  } catch (e: any) {
    errorMessage.value = e.message || '加载请求列表失败'
  } finally {
    isLoading.value = false
  }
}

async function loadAll() {
  await Promise.all([loadStats(), loadRequests()])
}

async function cancelRequest(requestId: string) {
  try {
    await apiClient.cancelRequest(requestId)
    await loadAll()
  } catch (e: any) {
    errorMessage.value = e.message || '取消请求失败'
  }
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'bg-orange-10 text-orange',
    running: 'bg-blue-10 text-blue',
    completed: 'bg-green-10 text-green',
    cancelled: 'bg-gray-10 text-muted',
    failed: 'bg-red-10 text-red',
    timeout: 'bg-red-10 text-red'
  }
  return colors[status] || 'bg-gray-10 text-muted'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    cancelled: '已取消',
    failed: '失败',
    timeout: '超时'
  }
  return labels[status] || status
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadAll()
  refreshInterval = window.setInterval(() => {
    if (autoRefresh.value) {
      loadAll()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<template>
  <div class="requests-page">
    <div class="container">
      <div class="page-header">
        <div class="header-row">
          <div>
            <h1>请求监控</h1>
            <p class="text-gray">实时监控 API 请求状态和系统资源使用情况</p>
          </div>
          <div class="header-actions">
            <label class="toggle-label">
              <input type="checkbox" v-model="autoRefresh" class="toggle-input" />
              <span class="toggle-text">自动刷新</span>
            </label>
            <button class="btn-secondary" @click="loadAll">🔄 刷新</button>
          </div>
        </div>
      </div>

      <div v-if="errorMessage" class="error-message">
        <span>⚠️</span>
        {{ errorMessage }}
      </div>

      <div v-if="stats" class="stats-grid">
        <div class="stat-card card">
          <div class="stat-icon text-blue">📊</div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.total_requests || 0 }}</div>
            <div class="stat-label">总请求数</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon text-green">✅</div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.active_requests || 0 }}</div>
            <div class="stat-label">活跃请求</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon text-orange">⏳</div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.queued_requests || 0 }}</div>
            <div class="stat-label">排队请求</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon text-red">❌</div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.failed_requests || 0 }}</div>
            <div class="stat-label">失败请求</div>
          </div>
        </div>
      </div>

      <div v-if="stats" class="system-info card">
        <h3 class="uppercase-label">系统信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">并发限制</span>
            <span class="info-value">{{ stats.max_concurrent || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">内存使用</span>
            <span class="info-value">{{ stats.memory_usage || '-' }} MB</span>
          </div>
          <div class="info-item">
            <span class="info-label">平均响应时间</span>
            <span class="info-value">{{ stats.avg_response_time ? formatDuration(stats.avg_response_time) : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">服务器时间</span>
            <span class="info-value">{{ stats.timestamp ? formatDate(stats.timestamp) : '-' }}</span>
          </div>
        </div>
      </div>

      <div class="requests-section">
        <div class="section-header">
          <h2>最近请求</h2>
          <span class="micro-label">共 {{ requests.length }} 条记录</span>
        </div>

        <div v-if="isLoading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="requests.length === 0" class="empty-state card">
          <div class="empty-icon">📭</div>
          <h3>暂无请求记录</h3>
          <p class="text-gray">开始分析后，请求记录将显示在这里</p>
        </div>

        <div v-else class="requests-list">
          <div
            v-for="req in requests.slice(0, 20)"
            :key="req.request_id"
            class="request-item card"
          >
            <div class="request-header">
              <div class="request-id">
                <code>{{ req.request_id?.slice(0, 24) }}...</code>
              </div>
              <span class="badge" :class="getStatusColor(req.status)">
                {{ getStatusLabel(req.status) }}
              </span>
            </div>

            <div class="request-meta">
              <div class="meta-item">
                <span class="meta-label">用户</span>
                <span class="meta-value">{{ req.person_id?.slice(0, 12) || '-' }}...</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">创建时间</span>
                <span class="meta-value">{{ req.created_at ? formatDate(req.created_at) : '-' }}</span>
              </div>
              <div v-if="req.duration_ms" class="meta-item">
                <span class="meta-label">耗时</span>
                <span class="meta-value">{{ formatDuration(req.duration_ms) }}</span>
              </div>
              <div v-if="req.current_stage" class="meta-item">
                <span class="meta-label">当前阶段</span>
                <span class="meta-value">{{ req.current_stage }}</span>
              </div>
            </div>

            <div v-if="req.progress !== undefined" class="request-progress">
              <div class="progress-header">
                <span class="micro-label">进度</span>
                <span class="micro-label">{{ req.progress }}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-bar-fill" :style="{ width: `${req.progress}%` }"></div>
              </div>
            </div>

            <div v-if="req.status === 'running' || req.status === 'pending'" class="request-actions">
              <button class="btn-ghost" @click="cancelRequest(req.request_id)">
                取消请求
              </button>
            </div>

            <div v-if="req.error_message" class="request-error">
              <span class="micro-label">错误信息:</span>
              <p>{{ req.error_message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  padding: var(--space-48) 0 var(--space-32);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-row h1 {
  margin-bottom: var(--space-8);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-16);
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  cursor: pointer;
  font-size: 14px;
  color: var(--color-gray-700);
}

.toggle-input {
  width: auto;
  margin: 0;
}

.error-message {
  background-color: rgba(238, 29, 54, 0.1);
  color: var(--color-red);
  padding: var(--space-12) var(--space-16);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-24);
  display: flex;
  align-items: center;
  gap: var(--space-8);
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-16);
  margin-bottom: var(--space-24);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--space-16);
  padding: var(--space-20);
}

.stat-icon {
  font-size: 32px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
  color: var(--color-near-black);
}

.stat-label {
  font-size: 13px;
  color: var(--color-gray-300);
}

.system-info {
  margin-bottom: var(--space-32);
}

.system-info h3 {
  margin-bottom: var(--space-16);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-16);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.info-label {
  font-size: 12px;
  color: var(--color-gray-300);
}

.info-value {
  font-weight: 500;
}

.requests-section {
  margin-top: var(--space-32);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-16);
}

.section-header h2 {
  font-size: 20px;
  margin-bottom: 0;
}

.loading-state {
  text-align: center;
  padding: var(--space-48);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-gray);
  border-top-color: var(--color-webflow-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto var(--space-16);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  text-align: center;
  padding: var(--space-48) var(--space-32);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-16);
}

.empty-state h3 {
  margin-bottom: var(--space-8);
}

.empty-state p {
  margin-bottom: 0;
}

.requests-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-16);
}

.request-item {
  padding: var(--space-20);
}

.request-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-16);
}

.request-meta {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-12);
  margin-bottom: var(--space-16);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.meta-label {
  font-size: 12px;
  color: var(--color-gray-300);
}

.meta-value {
  font-size: 14px;
  font-weight: 500;
}

.request-progress {
  margin-bottom: var(--space-16);
  padding-top: var(--space-12);
  border-top: 1px solid var(--color-border-gray);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-8);
}

.request-actions {
  padding-top: var(--space-12);
  border-top: 1px solid var(--color-border-gray);
  display: flex;
  justify-content: flex-end;
}

.request-error {
  padding: var(--space-12) var(--space-16);
  background-color: rgba(238, 29, 54, 0.05);
  border-radius: var(--radius-md);
  margin-top: var(--space-12);
}

.request-error p {
  margin-bottom: 0;
  color: var(--color-red);
  font-size: 14px;
}

@media (max-width: 992px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .request-meta {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-16);
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .request-meta {
    grid-template-columns: 1fr;
  }

  .request-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-12);
  }
}
</style>
