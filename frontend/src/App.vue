<script setup lang="ts">
import { ref } from 'vue'

const isMenuOpen = ref(false)

const navItems = [
  { path: '/', label: '首页' },
  { path: '/analyze', label: '智能分析' },
  { path: '/users', label: '用户管理' },
  { path: '/requests', label: '请求监控' }
]
</script>

<template>
  <div class="app-container">
    <header class="header">
      <div class="container header-content">
        <div class="logo">
          <span class="logo-icon">✦</span>
          <span class="logo-text">SlimCheck</span>
        </div>

        <nav class="nav-desktop">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            active-class="nav-link-active"
          >
            {{ item.label }}
          </router-link>
        </nav>

        <button class="btn-icon menu-toggle" @click="isMenuOpen = !isMenuOpen">
          <span v-if="!isMenuOpen">☰</span>
          <span v-else>✕</span>
        </button>
      </div>

      <div v-if="isMenuOpen" class="nav-mobile">
        <div class="container">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-link-mobile"
            @click="isMenuOpen = false"
          >
            {{ item.label }}
          </router-link>
        </div>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="footer">
      <div class="container footer-content">
        <div class="footer-left">
          <span class="logo-text">SlimCheck</span>
          <span class="micro-label">智能卡路里管理系统</span>
        </div>
        <div class="footer-right">
          <span class="caption">Built with LangGraph + Vue 3</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  border-bottom: 1px solid var(--color-border-gray);
  background-color: var(--color-white);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-16) var(--space-24);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.logo-icon {
  font-size: 24px;
  color: var(--color-webflow-blue);
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-near-black);
  letter-spacing: -0.4px;
}

.nav-desktop {
  display: flex;
  align-items: center;
  gap: var(--space-32);
}

.nav-link {
  font-size: var(--font-size-body-standard);
  font-weight: 500;
  color: var(--color-gray-700);
  padding: var(--space-8) 0;
  position: relative;
  transition: color var(--transition-fast);
}

.nav-link:hover {
  color: var(--color-near-black);
}

.nav-link-active {
  color: var(--color-webflow-blue);
}

.nav-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: var(--color-webflow-blue);
}

.menu-toggle {
  display: none;
}

.nav-mobile {
  display: none;
  border-top: 1px solid var(--color-border-gray);
  padding: var(--space-16) 0;
}

.nav-link-mobile {
  display: block;
  padding: var(--space-12) var(--space-16);
  color: var(--color-gray-700);
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: background-color var(--transition-fast);
}

.nav-link-mobile:hover {
  background-color: rgba(0, 0, 0, 0.04);
  color: var(--color-near-black);
}

.main-content {
  flex: 1;
}

.footer {
  border-top: 1px solid var(--color-border-gray);
  margin-top: auto;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-24);
}

.footer-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.caption {
  font-size: var(--font-size-caption);
  color: var(--color-gray-300);
}

@media (max-width: 768px) {
  .nav-desktop {
    display: none;
  }

  .menu-toggle {
    display: flex;
  }

  .nav-mobile {
    display: block;
  }

  .footer-content {
    flex-direction: column;
    gap: var(--space-16);
    text-align: center;
  }
}
</style>
