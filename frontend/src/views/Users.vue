<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient, type UserProfile } from '@/api/client'

const users = ref<UserProfile[]>([])
const isLoading = ref(false)
const showRegisterForm = ref(false)
const errorMessage = ref('')

const newUser = ref({
  gender: 'male' as 'male' | 'female',
  age: 30,
  height: 170,
  weight: 70,
  activity_level: 'moderate',
  name: ''
})

async function loadUsers() {
  isLoading.value = true
  try {
    users.value = await apiClient.listUsers()
  } catch (e: any) {
    errorMessage.value = e.message || '加载用户列表失败'
  } finally {
    isLoading.value = false
  }
}

async function registerUser() {
  try {
    const created = await apiClient.registerUser({
      gender: newUser.value.gender,
      age: newUser.value.age,
      height_cm: newUser.value.height,
      weight_kg: newUser.value.weight,
      activity_level: newUser.value.activity_level,
      name: newUser.value.name
    })
    users.value.unshift(created)
    showRegisterForm.value = false
    errorMessage.value = ''
    newUser.value = {
      gender: 'male',
      age: 30,
      height: 170,
      weight: 70,
      activity_level: 'moderate',
      name: ''
    }
  } catch (e: any) {
    errorMessage.value = e.message || '注册用户失败'
  }
}

async function deleteUser(personId: string) {
  if (!confirm('确定要删除此用户吗？')) return
  try {
    await apiClient.deleteUser(personId)
    users.value = users.value.filter((u: UserProfile) => u.person_id !== personId)
  } catch (e: any) {
    errorMessage.value = e.message || '删除用户失败'
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
}

function getActivityLabel(level: string): string {
  const labels: Record<string, string> = {
    sedentary: '久坐不动',
    light: '轻度活动',
    moderate: '中度活动',
    active: '高度活动',
    very_active: '极高活动'
  }
  return labels[level] || level
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="users-page">
    <div class="container">
      <div class="page-header">
        <div class="header-row">
          <div>
            <h1>用户管理</h1>
            <p class="text-gray">管理用户档案，设置个人健康参数</p>
          </div>
          <button class="btn-primary" @click="showRegisterForm = !showRegisterForm">
            {{ showRegisterForm ? '取消' : '+ 新增用户' }}
          </button>
        </div>
      </div>

      <div v-if="errorMessage" class="error-message">
        <span>⚠️</span>
        {{ errorMessage }}
      </div>

      <div v-if="showRegisterForm" class="register-form card">
        <h3>注册新用户</h3>
        <div class="form-grid">
          <div class="form-group">
            <label class="uppercase-label">姓名（可选）</label>
            <input v-model="newUser.name" type="text" placeholder="用户姓名" />
          </div>
          <div class="form-group">
            <label class="uppercase-label">性别</label>
            <select v-model="newUser.gender">
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
          <div class="form-group">
            <label class="uppercase-label">年龄</label>
            <input v-model.number="newUser.age" type="number" min="1" max="120" />
          </div>
          <div class="form-group">
            <label class="uppercase-label">身高 (cm)</label>
            <input v-model.number="newUser.height" type="number" min="50" max="250" />
          </div>
          <div class="form-group">
            <label class="uppercase-label">体重 (kg)</label>
            <input v-model.number="newUser.weight" type="number" min="1" max="300" />
          </div>
          <div class="form-group">
            <label class="uppercase-label">活动水平</label>
            <select v-model="newUser.activity_level">
              <option value="sedentary">久坐不动</option>
              <option value="light">轻度活动</option>
              <option value="moderate">中度活动</option>
              <option value="active">高度活动</option>
              <option value="very_active">极高活动</option>
            </select>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-secondary" @click="showRegisterForm = false">取消</button>
          <button class="btn-primary" @click="registerUser">确认注册</button>
        </div>
      </div>

      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="users.length === 0" class="empty-state card">
        <div class="empty-icon">👤</div>
        <h3>暂无用户</h3>
        <p class="text-gray">点击上方按钮注册第一个用户，开始使用健康分析功能</p>
      </div>

      <div v-else class="users-grid">
        <div v-for="user in users" :key="user.person_id" class="user-card card">
          <div class="user-header">
            <div class="user-avatar">
              {{ (user.name || 'U').charAt(0).toUpperCase() }}
            </div>
            <div class="user-info">
              <div class="user-name">{{ user.name || '未命名用户' }}</div>
              <div class="user-id" @click="copyToClipboard(user.person_id)">
                <code>{{ user.person_id.slice(0, 12) }}...</code>
                <span class="copy-hint micro-label">点击复制</span>
              </div>
            </div>
            <button class="btn-ghost delete-btn" @click="deleteUser(user.person_id)">
              🗑️
            </button>
          </div>

          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-label">性别</span>
              <span class="stat-value">{{ user.gender === 'male' ? '男' : '女' }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">年龄</span>
              <span class="stat-value">{{ user.age }} 岁</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">身高</span>
              <span class="stat-value">{{ user.height_cm }} cm</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">体重</span>
              <span class="stat-value">{{ user.weight_kg }} kg</span>
            </div>
          </div>

          <div v-if="user.bmr || user.daily_calorie_needs" class="user-calories">
            <div class="calorie-item">
              <span class="calorie-label">BMR 基础代谢</span>
              <span class="calorie-value text-blue">{{ Math.round(user.bmr || 0) }} kcal</span>
            </div>
            <div class="calorie-item">
              <span class="calorie-label">每日需求</span>
              <span class="calorie-value text-green">{{ Math.round(user.daily_calorie_needs || 0) }} kcal</span>
            </div>
          </div>

          <div v-if="user.health_assessment" class="user-health">
            <span class="health-label">健康评估</span>
            <span class="health-value">{{ user.health_assessment }}</span>
          </div>

          <div class="user-footer">
            <span class="micro-label">活动水平: {{ getActivityLabel(user.activity_level || 'moderate') }}</span>
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

.page-header h1 {
  margin-bottom: var(--space-8);
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

.register-form {
  margin-bottom: var(--space-32);
}

.register-form h3 {
  margin-bottom: var(--space-24);
  font-size: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-16);
  margin-bottom: var(--space-24);
}

.form-group {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: var(--space-8);
}

.form-group input,
.form-group select {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-12);
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

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: var(--space-24);
}

.user-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-20);
  padding: var(--space-24) !important;
}

.user-header {
  display: flex;
  align-items: center;
  gap: var(--space-16);
}

.user-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background-color: var(--color-webflow-blue);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 20px;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 600;
  font-size: 17px;
  margin-bottom: var(--space-6);
}

.user-id {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  cursor: pointer;
}

.copy-hint {
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.user-id:hover .copy-hint {
  opacity: 1;
}

.delete-btn {
  padding: var(--space-10);
}

.user-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-12);
}

.stat-item {
  text-align: center;
  padding: var(--space-12) var(--space-8);
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-md);
}

.stat-item .stat-label {
  display: block;
  font-size: 12px;
  color: var(--color-gray-300);
  margin-bottom: var(--space-8);
}

.stat-item .stat-value {
  font-weight: 600;
  font-size: 15px;
}

.user-calories {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-16);
  padding-top: var(--space-16);
  border-top: 1px solid var(--color-border-gray);
}

.calorie-item {
  text-align: center;
  padding: var(--space-8) 0;
}

.calorie-label {
  display: block;
  font-size: 13px;
  color: var(--color-gray-300);
  margin-bottom: var(--space-8);
}

.calorie-value {
  font-weight: 600;
  font-size: 17px;
}

.user-health {
  padding-top: var(--space-16);
  border-top: 1px solid var(--color-border-gray);
}

.health-label {
  display: block;
  font-size: 13px;
  color: var(--color-gray-300);
  margin-bottom: var(--space-8);
}

.health-value {
  font-size: 14px;
  color: var(--color-near-black);
}

.user-footer {
  padding-top: var(--space-16);
  border-top: 1px solid var(--color-border-gray);
  text-align: center;
}

@media (max-width: 768px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-16);
  }

  .header-row button {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .users-grid {
    grid-template-columns: 1fr;
  }

  .user-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
