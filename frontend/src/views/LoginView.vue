<script setup lang="ts">
import { reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const form = reactive({ username: '', password: '' })

async function submit() {
  const { data } = await login(form)
  auth.setSession(data)
  router.push((route.query.redirect as string) || '/dashboard')
}
</script>

<template>
  <main class="gm-auth-page">
    <section class="gm-auth-panel">
      <h1>登录</h1>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit">登录</el-button>
        <RouterLink to="/register">注册教师账号</RouterLink>
      </el-form>
    </section>
  </main>
</template>
