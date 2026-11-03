<script setup lang="ts">
import { onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, write } from "../api";
import Icon from "../components/Icon.vue";
const route = useRoute(), router = useRouter();
const email = ref(""), code = ref(""), error = ref(route.query.unavailable ? "暂时无法连接小站，请稍后再试" : "");
const message = ref(""), sending = ref(false), busy = ref(false), seconds = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;
function cooldown() {
  seconds.value = 60;
  clearInterval(timer);
  timer = setInterval(() => { if (--seconds.value <= 0) clearInterval(timer); }, 1000);
}
onUnmounted(() => clearInterval(timer));
async function send() {
  error.value = "";
  message.value = "";
  if (!/^[1-9][0-9]{4,10}@qq\.com$/i.test(email.value.trim())) {
    error.value = "请输入 QQ 号码对应的邮箱，例如 123456@qq.com";
    return;
  }
  sending.value = true;
  try {
    const result = await api<{message: string}>("/visitor/code", write("POST", {email: email.value}));
    message.value = result.message;
    code.value = "";
    cooldown();
  } catch (e) { error.value = (e as Error).message; }
  finally { sending.value = false; }
}
async function login() {
  busy.value = true;
  error.value = "";
  try {
    await api("/visitor/login", write("POST", {email: email.value, code: code.value}));
    const next = typeof route.query.next === "string" ? route.query.next : "/";
    await router.replace(next.startsWith("/") && !next.startsWith("//") && !next.includes("\\") && !/^\/(enter|login|admin)(\/|\?|$)/.test(next) ? next : "/");
  } catch(e) { error.value = (e as Error).message; }
  finally { busy.value = false; }
}
</script>

<template>
  <div class="private-entry">
    <div class="private-wordmark">LOVE.C <span>ONLY YOU &amp; ME</span></div>
    <form class="private-panel" @submit.prevent="login">
      <div class="private-seal"><Icon name="heart" :size="30" /></div>
      <p class="section-kicker">OUR PRIVATE LITTLE WORLD</p>
      <h1>只属于我们的世界</h1>
      <p class="private-intro">把日常留给彼此，把心动藏在这里。<br />验证你的 QQ 邮箱，一起回家。</p>
      <label>QQ 邮箱<input v-model.trim="email" type="email" required maxlength="18" autocomplete="email" placeholder="你的 QQ 号码@qq.com" :disabled="busy || sending" /></label>
      <div><label for="login-code">邮箱验证码</label><div class="private-code"><input id="login-code" v-model.trim="code" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" minlength="6" required autocomplete="one-time-code" placeholder="6 位验证码" :disabled="busy" /><button type="button" class="button secondary" :disabled="sending || busy || seconds > 0" @click="send">{{ sending ? '发送中…' : seconds > 0 ? `${seconds} 秒后重发` : '获取验证码' }}</button></div></div>
      <p v-if="message" class="private-hint" role="status">{{ message }}</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <button class="button private-submit" :disabled="busy || sending"><Icon name="lock" :size="17" />{{ busy ? '正在验证…' : '验证并进入小站' }}</button>
      <p class="private-hint">仅限我们两人的 QQ 邮箱 · 验证码 5 分钟内有效</p>
    </form>
    <p class="private-bottom">两个人的小世界，慢慢记录，好好珍藏。</p>
    <RouterLink to="/login" class="private-admin">管理入口</RouterLink>
  </div>
</template>

<style scoped>
.private-entry { min-height: 100svh; display: flex; align-items: center; flex-direction: column; justify-content: center; padding: 80px 20px 40px; background: radial-gradient(ellipse at 15% 20%, #f7e4e488, transparent 48%), radial-gradient(ellipse at 90% 80%, #eae3df88, transparent 45%), #fdfbf9; }
.private-wordmark { position: absolute; top: 28px; left: 32px; font-weight: 700; letter-spacing: 2px; }
.private-wordmark span { display: block; font-size: 8px; margin-top: 6px; color: #b2a39b; letter-spacing: 2.6px; }
.private-panel { width: min(100%, 440px); background: #ffffffdd; border: 1px solid #efe6e2; box-shadow: 0 14px 60px #72534c08; border-radius: 18px; padding: 36px; display: grid; gap: 20px; }
.private-seal { margin: auto; width: 66px; height: 66px; border-radius: 50%; background: #fcf0f1; color: #d68797; display: grid; place-items: center; }
.private-panel h1 { font-family: var(--serif); font-size: 25px; font-weight: 500; text-align: center; }
.private-panel .section-kicker { font-size: 9px; letter-spacing: 2px; text-align: center; margin: 0; }
.private-intro { text-align: center; color: #9a8e88; font-size: 13px; line-height: 1.9; margin-bottom: 8px; }
.private-panel label { font-size: 13px; }
.private-panel input { margin-top: 9px; background: #fdfcfb; }
.private-code { display: flex; align-items: center; gap: 10px; }
.private-code input { min-width: 0; flex: 1; }
.private-code button { margin-top: 9px; white-space: nowrap; padding: 12px; font-size: 12px; }
.private-submit { width: 100%; }
.private-hint { font-size: 11px; color: #9a8e88; line-height: 1.8; text-align: center; }
.private-bottom { font-size: 11px; letter-spacing: 1px; margin-top: 28px; color: #ad9e96; }
.private-admin { margin-top: 20px; font-size: 11px; color: #ad9e96; }
@media(max-width: 480px) { .private-panel { padding: 30px 22px; } .private-wordmark { left: 22px; top: 22px; } }
</style>
