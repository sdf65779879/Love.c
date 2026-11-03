<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { api, write } from "../api";
import Icon from "../components/Icon.vue";
const router = useRouter(),
  form = reactive({ username: "", password: "" }),
  error = ref(""),
  busy = ref(false);
async function login() {
  error.value = "";
  busy.value = true;
  try {
    await api("/auth/login", write("POST", form));
    await router.replace("/admin");
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <div class="login-wrap">
    <form class="login-panel panel" @submit.prevent="login">
      <span class="login-heart"><Icon name="heart" :size="32" /></span>
      <p class="section-kicker">WELCOME HOME</p>
      <h1>管理我们的小世界</h1>
      <p class="muted">用心记录，好好珍藏。</p>
      <label
        >管理员账号<input
          v-model="form.username"
          required
          autocomplete="username"
          placeholder="请输入管理员账号"
          maxlength="50" /></label
      ><label
        >密码<input
          v-model="form.password"
          type="password"
          required
          autocomplete="current-password"
          placeholder="请输入密码"
          maxlength="200"
      /></label>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <button class="button" :disabled="busy">
        <Icon name="lock" :size="17" />{{
          busy ? "正在回家…" : "进入小站管理"
        }}</button
      ><RouterLink to="/" class="text-link">← 回到小站首页</RouterLink>
    </form>
  </div>
</template>
