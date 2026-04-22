<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  {
    icon: '🧠',
    title: '多智能体协同',
    description: '饮食分析师、运动分析师、健康经理多智能体并行工作，提供精准分析',
    color: 'blue'
  },
  {
    icon: '⚡',
    title: '流式实时输出',
    description: '基于 SSE 实时推送分析进度和中间结果，无需等待完整响应',
    color: 'green'
  },
  {
    icon: '📊',
    title: '智能数据可视化',
    description: '自动识别饮食和运动数据，结构化展示卡路里摄入与消耗',
    color: 'purple'
  },
  {
    icon: '🛡️',
    title: '请求智能管理',
    description: '支持请求取消、并发控制、超时保护，节约 LLM API 资源',
    color: 'orange'
  }
]

const stats = [
  { value: '5', label: '专业智能体', suffix: '个' },
  { value: '1000+', label: '每日可处理', suffix: '次' },
  { value: '< 30s', label: '平均响应', suffix: '' }
]
</script>

<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="container">
        <div class="hero-content">
          <div class="badge">v1.0 正式发布</div>
          <h1 class="hero-title">
            智能卡路里
            <span class="text-blue">管理系统</span>
          </h1>
          <p class="hero-subtitle">
            基于 LangGraph 多智能体架构，实时分析饮食与运动数据，
            帮助您科学管理卡路里摄入与消耗。
          </p>
          <div class="hero-actions">
            <button class="btn-primary" @click="router.push('/analyze')">
              开始分析 →
            </button>
            <button class="btn-secondary" @click="router.push('/users')">
              管理用户
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div v-for="stat in stats" :key="stat.label" class="stat-item">
            <div class="stat-value">{{ stat.value }}<span class="stat-suffix">{{ stat.suffix }}</span></div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="features-section">
      <div class="container">
        <div class="section-header">
          <span class="uppercase-label">核心功能</span>
          <h2>强大的分析能力</h2>
          <p class="section-description">
            采用先进的多智能体协同技术，为您提供专业级的健康管理体验
          </p>
        </div>

        <div class="features-grid">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="feature-card card"
          >
            <div class="feature-icon" :class="`bg-${feature.color}-10`">
              {{ feature.icon }}
            </div>
            <h3>{{ feature.title }}</h3>
            <p class="text-gray">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="cta-section">
      <div class="container">
        <div class="cta-content card">
          <div>
            <h2>准备好开始了吗？</h2>
            <p class="text-gray">立即体验智能卡路里分析，让健康管理更科学</p>
          </div>
          <button class="btn-primary" @click="router.push('/analyze')">
            立即体验
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero-section {
  padding: var(--space-64) 0;
  text-align: center;
}

.hero-content {
  max-width: 700px;
  margin: 0 auto;
}

.badge {
  margin-bottom: var(--space-24);
}

.hero-title {
  font-size: var(--font-size-display-hero);
  font-weight: 600;
  line-height: 1.04;
  letter-spacing: -0.8px;
  margin-bottom: var(--space-24);
}

.hero-subtitle {
  font-size: var(--font-size-body);
  line-height: var(--line-height-body);
  color: var(--color-gray-700);
  margin-bottom: var(--space-32);
}

.hero-actions {
  display: flex;
  gap: var(--space-16);
  justify-content: center;
  flex-wrap: wrap;
}

.stats-section {
  padding: var(--space-48) 0;
  border-top: 1px solid var(--color-border-gray);
  border-bottom: 1px solid var(--color-border-gray);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-32);
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 48px;
  font-weight: 600;
  color: var(--color-near-black);
  line-height: 1.1;
  margin-bottom: var(--space-8);
}

.stat-suffix {
  font-size: 24px;
  color: var(--color-gray-300);
  margin-left: var(--space-4);
}

.stat-label {
  font-size: var(--font-size-body-standard);
  color: var(--color-gray-700);
}

.features-section {
  padding: var(--space-64) 0;
}

.section-header {
  text-align: center;
  max-width: 600px;
  margin: 0 auto var(--space-48);
}

.section-header .uppercase-label {
  display: inline-block;
  margin-bottom: var(--space-16);
}

.section-header h2 {
  margin-bottom: var(--space-16);
}

.section-description {
  font-size: var(--font-size-body);
  color: var(--color-gray-700);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-24);
}

.feature-card {
  text-align: left;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: var(--space-16);
}

.feature-card h3 {
  margin-bottom: var(--space-8);
}

.feature-card p {
  margin-bottom: 0;
}

.cta-section {
  padding: var(--space-64) 0;
}

.cta-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-32);
  padding: var(--space-32);
}

.cta-content h2 {
  margin-bottom: var(--space-8);
}

.cta-content p {
  margin-bottom: 0;
}

@media (max-width: 992px) {
  .hero-title {
    font-size: 56px;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 40px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--space-24);
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .cta-content {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 479px) {
  .hero-title {
    font-size: 32px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .hero-actions button {
    width: 100%;
  }

  .stat-value {
    font-size: 36px;
  }
}
</style>
