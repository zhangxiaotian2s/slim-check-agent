<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { apiClient, type FoodItem, type ExerciseItem, type HealthReview, type StreamController, type ThinkingEvent, type ResultEvent, type StatusEvent, type FoodItemsData, type ExerciseItemsData } from '@/api/client'

const textInput = ref('')
const personId = ref('')
const isAnalyzing = ref(false)
const progress = ref(0)
const currentStage = ref('')
const requestId = ref('')
const streamController = ref<StreamController | null>(null)
const showThinking = ref(true)

// 图片上传相关
const selectedImage = ref<File | null>(null)
const imagePreview = ref<string>('')
const inputMode = ref<'text' | 'image' | 'both'>('text')

const foodItems = ref<FoodItem[]>([])
const exerciseItems = ref<ExerciseItem[]>([])
const healthReview = ref<HealthReview | null>(null)
const errorMessage = ref('')
const thinkingHistory = ref<Array<{ stage: string; content: string; timestamp: Date }>>([])

const STAGE_NAMES: Record<string, string> = {
  initializing: '初始化中',
  route_input: '识别输入类型',
  classify_text: '分析文本内容',
  check_user_info: '检查用户信息',
  analyze_diet: '饮食数据分析',
  analyze_exercise: '运动数据分析',
  health_review: '健康综合评估',
  generate_result: '生成最终报告',
  completed: '分析完成',
  error: '分析失败',
  cancelled: '已取消'
}

const STAGE_ICONS: Record<string, string> = {
  route_input: '🔍',
  classify_text: '📝',
  check_user_info: '👤',
  analyze_diet: '🥗',
  analyze_exercise: '🏃',
  health_review: '💡',
  generate_result: '📊',
  completed: '✅',
  error: '❌',
  cancelled: '⚠️'
}

function generateRequestId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

function addThinking(stage: string, content: string) {
  thinkingHistory.value.push({
    stage,
    content,
    timestamp: new Date()
  })

  // 处理错误阶段 - 确保错误状态正确更新
  if (stage === 'error') {
    isAnalyzing.value = false
    progress.value = 100
    currentStage.value = STAGE_NAMES['error'] || '分析失败'
    if (!errorMessage.value) {
      errorMessage.value = content.replace(/^❌\s*/, '') || '分析过程中发生错误'
    }
  }
}

// 图片选择处理
function handleImageSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    errorMessage.value = '请选择有效的图片文件'
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    errorMessage.value = '图片大小不能超过 10MB'
    return
  }

  selectedImage.value = file
  errorMessage.value = ''

  // 生成预览
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

// 移除图片
function removeImage() {
  selectedImage.value = null
  imagePreview.value = ''
}

// 图片转 base64
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // 移除 data:image/xxx;base64, 前缀
      const base64 = result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

async function startAnalysis() {
  if (!personId.value.trim()) {
    errorMessage.value = '请输入用户 ID'
    return
  }

  // 验证输入：至少需要文字或图片
  const hasText = textInput.value.trim().length > 0
  const hasImage = selectedImage.value !== null

  if (!hasText && !hasImage) {
    errorMessage.value = '请输入分析内容或上传图片'
    return
  }

  errorMessage.value = ''
  foodItems.value = []
  exerciseItems.value = []
  healthReview.value = null
  thinkingHistory.value = []
  isAnalyzing.value = true
  progress.value = 0
  currentStage.value = '初始化中'
  requestId.value = generateRequestId()

  // 确定输入类型
  let inputType: 'text_only' | 'image' | 'image_with_text' = 'text_only'
  if (hasImage && hasText) {
    inputType = 'image_with_text'
  } else if (hasImage) {
    inputType = 'image'
  }

  // 转换图片为 base64
  let imageBase64: string | undefined
  if (selectedImage.value) {
    imageBase64 = await fileToBase64(selectedImage.value)
  }

  streamController.value = apiClient.streamAnalysis(
    {
      input_type: inputType,
      text: textInput.value || undefined,
      image: imageBase64,
      person_id: personId.value
    },
    requestId.value,
    {
      onStatus: (data: StatusEvent) => {
        progress.value = data.progress
        currentStage.value = STAGE_NAMES[data.stage] || data.message

        // 处理错误阶段 - 确保分析状态正确更新
        if (data.stage === 'error') {
          isAnalyzing.value = false
        }
      },
      onThinking: (data: ThinkingEvent) => {
        addThinking(data.stage, data.content)
      },
      onResult: (data: ResultEvent) => {
        if (data.type === 'food_items') {
          const foodData = data.data as FoodItemsData
          foodItems.value = foodData.foods
          addThinking('analyze_diet', `✓ 识别到 ${foodData.foods.length} 种食物，总计 ${foodData.total_calories} kcal`)
        } else if (data.type === 'exercise_items') {
          const exerciseData = data.data as ExerciseItemsData
          exerciseItems.value = exerciseData.exercises
          addThinking('analyze_exercise', `✓ 识别到 ${exerciseData.exercises.length} 项运动，总计消耗 ${exerciseData.total_calories_burned} kcal`)
        } else if (data.type === 'health_review') {
          healthReview.value = data.data as HealthReview
          addThinking('health_review', '✓ 健康评估完成')
        }
      },
      onComplete: () => {
        isAnalyzing.value = false
        progress.value = 100
        currentStage.value = '分析完成'
        addThinking('completed', '🎉 分析完成！')
      },
      onError: (error: string) => {
        isAnalyzing.value = false
        progress.value = 100
        currentStage.value = STAGE_NAMES['error'] || '分析失败'
        errorMessage.value = error || '分析过程中发生错误'
        // 注意：如果后端已发送 thinking 事件，这里就不需要重复添加
        // 仅作为 fallback 确保前端能显示错误
        if (!thinkingHistory.value.find(t => t.stage === 'error')) {
          addThinking('error', `❌ ${error}`)
        }
      },
      onCancelled: () => {
        isAnalyzing.value = false
        progress.value = 100
        currentStage.value = STAGE_NAMES['cancelled'] || '已取消'
        // 注意：如果后端已发送 thinking 事件，这里就不需要重复添加
        if (!thinkingHistory.value.find(t => t.stage === 'cancelled')) {
          addThinking('cancelled', '⚠️ 用户取消了分析')
        }
      }
    }
  )
}

async function cancelAnalysis() {
  if (streamController.value) {
    streamController.value.cancel()
    streamController.value = null
  }
  if (requestId.value) {
    try {
      await apiClient.cancelRequest(requestId.value)
    } catch (e) {
      console.error('Cancel request failed:', e)
    }
  }
  isAnalyzing.value = false
  currentStage.value = '已取消'
}

function resetResults() {
  foodItems.value = []
  exerciseItems.value = []
  healthReview.value = null
  errorMessage.value = ''
  progress.value = 0
  currentStage.value = ''
  requestId.value = ''
  thinkingHistory.value = []
  selectedImage.value = null
  imagePreview.value = ''
}

function getCaloriesColor(net: number): string {
  if (net < 0) return 'text-green'
  if (net > 500) return 'text-red'
  return 'text-orange'
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function getFoodCalories(item: FoodItem): number {
  return item.calories
}

function getExerciseCalories(item: ExerciseItem): number {
  return item.calories_burned || item.calories || 0
}

function getExerciseDuration(item: ExerciseItem): number {
  return item.duration_minutes || item.duration || 0
}

onUnmounted(() => {
  if (streamController.value) {
    streamController.value.cancel()
  }
})

// 类型声明
const imageInput = ref<HTMLInputElement | null>(null)
</script>

<template>
  <div class="analyze-page">
    <div class="container">
      <div class="page-header">
        <h1>智能卡路里分析</h1>
        <p class="text-gray">输入饮食/运动描述或上传食物图片，AI 将实时分析并返回结构化结果</p>
      </div>

      <div class="analyze-grid">
        <!-- 左侧：输入表单 -->
        <div class="input-section card">
          <div class="form-group">
            <label class="uppercase-label">用户 ID</label>
            <input
              v-model="personId"
              type="text"
              placeholder="例如: fa65e4f5"
              :disabled="isAnalyzing"
            />
          </div>

          <div class="form-group">
            <label class="uppercase-label">输入模式</label>
            <div class="mode-tabs">
              <button
                class="mode-tab"
                :class="{ active: inputMode === 'text' }"
                @click="inputMode = 'text'"
                :disabled="isAnalyzing"
              >
                📝 仅文字
              </button>
              <button
                class="mode-tab"
                :class="{ active: inputMode === 'image' }"
                @click="inputMode = 'image'"
                :disabled="isAnalyzing"
              >
                📷 仅图片
              </button>
              <button
                class="mode-tab"
                :class="{ active: inputMode === 'both' }"
                @click="inputMode = 'both'"
                :disabled="isAnalyzing"
              >
                📝📷 文字+图片
              </button>
            </div>
          </div>

          <div v-if="inputMode !== 'image'" class="form-group">
            <label class="uppercase-label">分析内容</label>
            <textarea
              v-model="textInput"
              rows="6"
              placeholder="描述您的饮食和运动，例如：&#10;早餐吃了一个包子和一杯豆浆&#10;中午慢跑了30分钟&#10;晚餐吃了一份沙拉"
              :disabled="isAnalyzing"
            ></textarea>
          </div>

          <div v-if="inputMode !== 'text'" class="form-group">
            <label class="uppercase-label">上传图片</label>
            <div v-if="!imagePreview" class="image-upload-area" @click="imageInput?.click()">
              <div class="upload-icon">📷</div>
              <p class="upload-text">点击上传图片</p>
              <p class="upload-hint">支持 JPG、PNG 格式，最大 10MB</p>
              <input
                ref="imageInput"
                type="file"
                accept="image/*"
                style="display: none"
                @change="handleImageSelect"
                :disabled="isAnalyzing"
              />
            </div>
            <div v-else class="image-preview">
              <img :src="imagePreview" alt="预览图片" />
              <button
                v-if="!isAnalyzing"
                class="remove-image-btn"
                @click="removeImage"
              >
                ✕ 移除图片
              </button>
            </div>
          </div>

          <div v-if="errorMessage" class="error-message">
            <span>⚠️</span>
            {{ errorMessage }}
          </div>

          <div class="action-buttons">
            <button
              v-if="!isAnalyzing"
              class="btn-primary"
              @click="startAnalysis"
              :disabled="(!textInput.trim() && !selectedImage) || !personId.trim()"
            >
              开始分析
            </button>
            <button v-else class="btn-secondary" @click="cancelAnalysis">
              取消分析
            </button>
            <button
              v-if="!isAnalyzing && thinkingHistory.length > 0"
              class="btn-ghost"
              @click="resetResults"
            >
              清空结果
            </button>
          </div>

          <div v-if="isAnalyzing || progress > 0" class="progress-section">
            <div class="progress-header">
              <span class="micro-label">{{ currentStage }}</span>
              <span class="micro-label">{{ progress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-bar-fill" :style="{ width: `${progress}%` }"></div>
            </div>
            <div v-if="requestId" class="request-id">
              <span class="micro-label">请求 ID: {{ requestId.slice(0, 24) }}...</span>
            </div>
          </div>
        </div>

        <!-- 右侧：思考过程 + 结果 -->
        <div class="right-section">
          <div class="thinking-section card">
          <div class="thinking-header">
            <div class="thinking-title">
              <span>🧠</span>
              <span class="uppercase-label">思考过程</span>
            </div>
            <button class="toggle-btn" @click="showThinking = !showThinking">
              {{ showThinking ? '收起' : '展开' }}
            </button>
          </div>

          <div v-if="showThinking" class="thinking-content">
            <div v-if="thinkingHistory.length === 0" class="thinking-empty">
              <p class="text-gray">点击「开始分析」查看 AI 思考过程...</p>
            </div>
            <div v-else class="thinking-list">
              <div
                v-for="(item, index) in thinkingHistory"
                :key="index"
                class="thinking-item animate-slide-in"
              >
                <div class="thinking-meta">
                  <span class="thinking-icon">
                    {{ STAGE_ICONS[item.stage] || '🤔' }}
                  </span>
                  <span class="thinking-stage">
                    {{ STAGE_NAMES[item.stage] || item.stage }}
                  </span>
                  <span class="thinking-time">{{ formatTime(item.timestamp) }}</span>
                </div>
                <div class="thinking-content-text">
                  {{ item.content }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：结果展示 -->
        <div class="results-section">
          <div v-if="foodItems.length > 0" class="result-card card animate-slide-in">
            <div class="result-header">
              <span class="badge bg-green-10 text-green">🍽️ 饮食分析</span>
            </div>
            <div class="food-list">
              <div v-for="item in foodItems" :key="item.name" class="food-item">
                <div class="food-name">{{ item.name }}</div>
                <div class="food-details">
                  <span class="food-calories text-green">{{ getFoodCalories(item) }} kcal</span>
                  <span class="food-macro">蛋白质 {{ item.protein_g }}g · 碳水 {{ item.carbs_g }}g · 脂肪 {{ item.fat_g }}g</span>
                </div>
              </div>
            </div>
            <div class="result-total">
              <span class="uppercase-label">总摄入</span>
              <span class="total-value text-green">
                {{ foodItems.reduce((sum: number, item: FoodItem) => sum + getFoodCalories(item), 0) }} kcal
              </span>
            </div>
          </div>

          <div v-if="exerciseItems.length > 0" class="result-card card animate-slide-in">
            <div class="result-header">
              <span class="badge bg-orange-10 text-orange">🏃 运动分析</span>
            </div>
            <div class="exercise-list">
              <div v-for="item in exerciseItems" :key="item.name || item.type" class="exercise-item">
                <div class="exercise-name">{{ item.name || item.type }}</div>
                <div class="exercise-details">
                  <span class="exercise-calories text-orange">-{{ getExerciseCalories(item) }} kcal</span>
                  <span class="exercise-meta">{{ getExerciseDuration(item) }} 分钟 · {{ item.intensity }}</span>
                </div>
              </div>
            </div>
            <div class="result-total">
              <span class="uppercase-label">总消耗</span>
              <span class="total-value text-orange">
                {{ exerciseItems.reduce((sum: number, item: ExerciseItem) => sum + getExerciseCalories(item), 0) }} kcal
              </span>
            </div>
          </div>

          <div v-if="healthReview" class="result-card card animate-slide-in">
            <div class="result-header">
              <span class="badge bg-blue-10 text-blue">💡 健康评估</span>
            </div>
            <div class="health-summary">
              <div class="health-stats">
                <div class="health-stat">
                  <span class="stat-label">净卡路里</span>
                  <span class="stat-number" :class="getCaloriesColor(healthReview.net_calories)">
                    {{ healthReview.net_calories > 0 ? '+' : '' }}{{ healthReview.net_calories }} kcal
                  </span>
                </div>
                <div class="health-stat">
                  <span class="stat-label">蛋白质</span>
                  <span class="stat-number">
                    {{ healthReview.protein_current }}g / {{ healthReview.protein_goal }}g
                  </span>
                </div>
              </div>
              <div class="health-assessment">
                <h4>总体评估</h4>
                <p>{{ healthReview.overall_assessment }}</p>
              </div>
              <div class="health-recommendations">
                <h4>建议</h4>
                <ul>
                  <li v-for="(rec, index) in healthReview.recommendations" :key="index">
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div v-if="thinkingHistory.length === 0 && !isAnalyzing" class="empty-state card">
            <div class="empty-icon">✨</div>
            <h3>开始您的健康分析</h3>
            <p class="text-gray">输入饮食和运动描述，AI 将为您提供精准的卡路里分析</p>
          </div>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.page-header {
  padding: var(--space-48) 0 var(--space-32);
  text-align: center;
}

.page-header h1 {
  margin-bottom: var(--space-8);
}

.mode-tabs {
  display: flex;
  gap: var(--space-8);
  flex-wrap: wrap;
}

.mode-tab {
  flex: 1;
  min-width: 100px;
  padding: var(--space-10) var(--space-12);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  background: var(--color-white);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    border-color: var(--color-webflow-blue);
    background: rgba(20, 110, 245, 0.05);
  }

  &.active {
    border-color: var(--color-webflow-blue);
    background: var(--color-webflow-blue);
    color: white;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.image-upload-area {
  border: 2px dashed var(--color-gray-200);
  border-radius: var(--radius-md);
  padding: var(--space-32) var(--space-16);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--color-webflow-blue);
    background: rgba(20, 110, 245, 0.02);
  }
}

.upload-icon {
  font-size: 40px;
  margin-bottom: var(--space-12);
}

.upload-text {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 var(--space-4) 0;
}

.upload-hint {
  font-size: 12px;
  color: var(--color-gray-400);
  margin: 0;
}

.image-preview {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-gray-200);

  img {
    width: 100%;
    max-height: 300px;
    object-fit: contain;
    display: block;
  }
}

.remove-image-btn {
  position: absolute;
  top: var(--space-8);
  right: var(--space-8);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  padding: var(--space-6) var(--space-12);
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(220, 38, 38, 0.9);
  }
}

.analyze-grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: var(--space-24);
  align-items: start;
}

.input-section {
  position: sticky;
  top: 80px;
}

.right-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-24);
}

.thinking-section {
  max-height: 380px;
  display: flex;
  flex-direction: column;
}

.thinking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-16);
  padding-bottom: var(--space-12);
  border-bottom: 1px solid var(--color-border-gray);
}

.thinking-title {
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.toggle-btn {
  background: none;
  border: none;
  color: var(--color-webflow-blue);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}

.toggle-btn:hover {
  text-decoration: underline;
}

.thinking-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.thinking-empty {
  padding: var(--space-32) var(--space-16);
  text-align: center;
}

.thinking-empty p {
  font-size: 14px;
  margin: 0;
}

.thinking-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-12);
}

.thinking-item {
  padding: var(--space-12);
  background-color: rgba(20, 110, 245, 0.03);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-webflow-blue);
}

.thinking-meta {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  margin-bottom: var(--space-8);
}

.thinking-icon {
  font-size: 16px;
}

.thinking-stage {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-near-black);
}

.thinking-time {
  font-size: 11px;
  color: var(--color-gray-300);
  margin-left: auto;
}

.thinking-content-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-gray-700);
}

.form-group {
  margin-bottom: var(--space-24);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-8);
}

.form-group input,
.form-group textarea {
  width: 100%;
  resize: vertical;
}

.error-message {
  background-color: rgba(238, 29, 54, 0.1);
  color: var(--color-red);
  padding: var(--space-12) var(--space-16);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-16);
  display: flex;
  align-items: center;
  gap: var(--space-8);
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: var(--space-12);
  flex-wrap: wrap;
  margin-bottom: var(--space-24);
}

.action-buttons button {
  flex: 1;
  min-width: 120px;
}

.progress-section {
  padding-top: var(--space-16);
  border-top: 1px solid var(--color-border-gray);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-8);
}

.request-id {
  margin-top: var(--space-12);
  text-align: center;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-20);
}

.result-card {
  animation-delay: 0.1s;
}

.result-header {
  margin-bottom: var(--space-20);
}

.food-list,
.exercise-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-12);
  margin-bottom: var(--space-20);
}

.food-item,
.exercise-item {
  padding: var(--space-12) var(--space-16);
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-md);
}

.food-name,
.exercise-name {
  font-weight: 500;
  margin-bottom: var(--space-4);
}

.food-details,
.exercise-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-8);
}

.food-calories,
.exercise-calories {
  font-weight: 600;
  font-size: 18px;
}

.food-macro,
.exercise-meta {
  font-size: 13px;
  color: var(--color-gray-300);
}

.result-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-16);
  border-top: 1px solid var(--color-border-gray);
}

.total-value {
  font-size: 20px;
  font-weight: 600;
}

.health-summary {
  display: flex;
  flex-direction: column;
  gap: var(--space-20);
}

.health-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-16);
}

.health-stat {
  text-align: center;
  padding: var(--space-16);
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-md);
}

.health-stat .stat-label {
  display: block;
  font-size: 12px;
  color: var(--color-gray-300);
  margin-bottom: var(--space-8);
}

.health-stat .stat-number {
  font-size: 24px;
  font-weight: 600;
}

.health-assessment h4,
.health-recommendations h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: var(--space-8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.health-assessment p {
  margin-bottom: 0;
  line-height: 1.6;
}

.health-recommendations ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.health-recommendations li {
  padding: var(--space-8) 0;
  padding-left: var(--space-20);
  position: relative;
  color: var(--color-gray-700);
  font-size: 14px;
  line-height: 1.5;
}

.health-recommendations li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: var(--color-green);
  font-weight: bold;
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
  font-size: 18px;
}

.empty-state p {
  margin-bottom: 0;
    grid-column: 1 / -1;
    max-height: 400px;
  }

@media (max-width: 768px) {
  .analyze-grid {
    grid-template-columns: 1fr;
  }

  .input-section,
  .thinking-section {
    position: static;
  }

  .health-stats {
    grid-template-columns: 1fr;
  }

  .food-details,
  .exercise-details {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-4);
  }
}
</style>
