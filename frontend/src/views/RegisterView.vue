<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api/auth'

const router = useRouter()
const form = reactive({
  username: '',
  display_name: '',
  password: '',
  email: '',
  phone: '',
})

async function submit() {
  await register({
    ...form,
    email: form.email || null,
    phone: form.phone || null,
  })
  router.push('/login')
}
</script>

<template>
  <main class="gm-auth-page">
    <section class="gm-auth-panel">
      <h1>注册教师账号</h1>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="new-password" show-password />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" type="email" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-button type="primary" native-type="submit">注册</el-button>
        <RouterLink to="/login">已有账号，去登录</RouterLink>
      </el-form>
    </section>
  </main>
</template>
