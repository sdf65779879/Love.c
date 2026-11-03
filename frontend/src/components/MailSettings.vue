<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from "vue";
import { api, write } from "../api";
import { notify, state } from "../store";
type Config = { enabled: boolean; host: string; port: number; username: string; from_address: string; security: string; has_password: boolean; updated_at: string };
type Delivery = { id: number; event: string; recipient: string; status: string; detail: string; actor: string; created_at: string };
const form = reactive({ enabled: true, host: "smtp.qq.com", port: 465, username: "", from_address: "", security: "ssl", password: "" });
const loading = ref(true), saving = ref(false), sending = ref(false), error = ref(""), testError = ref(""), result = ref("");
const saved = ref<Config | null>(null), records = ref<Delivery[]>([]), partner = ref("boy");
const logError = ref("");
const payload = () => ({ enabled: form.enabled, host: form.host, port: form.port, username: form.username, from_address: form.from_address, security: form.security });
const dirty = computed(() => !!form.password || !saved.value || Object.entries(payload()).some(([key,value]) => saved.value?.[key as keyof Config] !== value));
const receiver = computed(() => partner.value === "boy" ? state.site?.boy_qq : state.site?.girl_qq);
const events: Record<string,string> = {LOGIN_CODE:"登录验证码", ANNIVERSARY_REMINDER:"纪念日提醒", SMTP_TEST:"测试邮件", SETTINGS_UPDATED:"修改邮箱配置"};
const statuses: Record<string,string> = {sent:"已提交", failed:"失败", saved:"已保存", sending:"发送中", uncertain:"提交结果待确认"};
let successTimer: ReturnType<typeof setTimeout> | undefined;
onUnmounted(() => clearTimeout(successTimer));
async function logs() {
  logError.value = "";
  try { records.value = await api<Delivery[]>("/admin/mail/deliveries"); }
  catch(e) { logError.value = (e as Error).message; }
}
async function load() {
  loading.value = true; error.value = "";
  try {
    saved.value = await api<Config>("/admin/mail");
    for (const key of Object.keys(payload())) (form as any)[key] = saved.value[key as keyof Config];
    form.password = "";
    await logs();
  } catch(e) { error.value = (e as Error).message; }
  finally { loading.value = false; }
}
async function save() {
  error.value = ""; saving.value = true;
  try {
    saved.value = await api<Config>("/admin/mail", write("PUT", {...payload(), password: form.password || null}));
    for (const key of Object.keys(payload())) (form as any)[key] = saved.value[key as keyof Config];
    form.password = "";
    notify("邮箱配置已保存，下一次发送立即生效");
    await logs();
  } catch(e) { error.value = (e as Error).message; }
  finally { saving.value = false; }
}
async function test() {
  if (dirty.value || sending.value) return;
  testError.value = ""; result.value = ""; sending.value = true;
  try {
    const response = await api<{message:string}>("/admin/mail/test", write("POST", {partner: partner.value}));
    result.value = response.message;
    clearTimeout(successTimer);
    successTimer = setTimeout(() => { result.value = ""; }, 8000);
  } catch(e) { testError.value = (e as Error).message; }
  finally { sending.value = false; await logs(); }
}
onMounted(load);
</script>

<template>
  <div v-if="loading" class="status-block"><span class="spinner"/>正在读取邮箱配置…</div>
  <div v-else-if="!saved" class="console-card"><p class="error-text" role="alert">{{ error }}</p><button class="button" @click="load">重新加载</button></div>
  <div v-else class="mail-column">
    <div class="console-card">
    <form class="settings-panel" @submit.prevent="save">
      <h1>系统邮箱设置</h1>
      <p class="settings-help">登录验证码、纪念日提醒和测试邮件统一使用此邮箱发送。QQ 邮箱需要开启 SMTP 服务，并使用 SMTP 授权码。</p>
      <label>系统邮件发送<select v-model="form.enabled" :disabled="saving || sending"><option :value="true">启用</option><option :value="false">停用</option></select></label>
      <label>SMTP 服务器<input v-model.trim="form.host" required maxlength="253" placeholder="smtp.qq.com" :disabled="saving || sending" /></label>
      <div class="couple-fields"><label>SMTP 端口<input v-model.number="form.port" type="number" min="1" max="65535" required :disabled="saving || sending" /></label>
      <label>连接加密<select v-model="form.security" :disabled="saving || sending"><option value="ssl">SSL / TLS（QQ 邮箱推荐 465）</option><option value="starttls">STARTTLS（通常为 587）</option></select></label></div>
      <label>发件邮箱账号<input v-model.trim="form.username" type="email" required maxlength="254" placeholder="你的发件QQ号码@qq.com" autocomplete="off" :disabled="saving || sending" /></label>
      <label>SMTP 授权码<input v-model="form.password" type="password" maxlength="500" autocomplete="new-password" :placeholder="saved.has_password ? '已配置，留空保留原授权码' : '请输入邮箱的 SMTP 授权码'" :disabled="saving || sending" /></label>
      <p class="settings-help">{{ saved.has_password ? '授权码已加密保存，不会回显。更换发件账号时需同时填写新授权码。' : '尚未配置授权码。这里填写 SMTP 授权码，不是 QQ 登录密码。' }}</p>
      <label>发件地址（可选）<input v-model.trim="form.from_address" type="email" maxlength="254" placeholder="留空使用发件邮箱账号" :disabled="saving || sending" /></label>
      <p v-if="!form.enabled" class="settings-help">停用后无法发送登录验证码，已有登录会话仍可使用，管理员仍可登录后台。</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="settings-actions"><button class="button" :disabled="saving || sending">{{ saving ? '保存中…' : '保存邮箱配置' }}</button></div>
    </form>
    <section class="settings-panel mail-test">
      <h2>登录邮件与测试</h2>
      <p class="settings-help">登录验证码只发送到情侣配置中的两个 QQ 邮箱。此处测试会使用当前已保存的系统邮箱，向你选择的一方发送一封真实测试邮件。</p>
      <label>测试收件人<select v-model="partner" :disabled="sending"><option value="boy">男主邮箱{{ state.site?.boy_qq ? ` · ${state.site.boy_qq}@qq.com` : ' · 尚未配置' }}</option><option value="girl">女主邮箱{{ state.site?.girl_qq ? ` · ${state.site.girl_qq}@qq.com` : ' · 尚未配置' }}</option></select></label>
      <p v-if="dirty" class="settings-help">存在未保存的修改，请先保存邮箱配置，再发送测试邮件。</p>
      <p v-if="!receiver" class="settings-help">请先在「基本设置 → 情侣配置」填写该方 QQ 号。</p>
      <p v-if="testError" class="error-text" role="alert">{{ testError }}</p>
      <p v-if="result" class="settings-help" role="status">{{ result }}</p>
      <button class="button secondary" :disabled="dirty || saving || sending || !saved.enabled || !saved.has_password || !receiver" @click="test">{{ sending ? '正在发送测试邮件…' : '发送测试邮件' }}</button>
      <p class="settings-help">测试邮件不包含登录验证码。发送成功代表邮件服务器已接受，请同时检查收件箱和垃圾邮件。失败时可查看下方记录；系统不会自动重复发送。</p>
    </section>
    </div>
    <section class="console-card settings-panel">
      <div class="section-row"><h2>最近投递与配置记录</h2><button class="text-link" @click="logs">刷新记录</button></div>
      <p class="settings-help">最近 30 条记录，邮箱地址已脱敏。记录不包含验证码、授权码或邮件正文。</p>
      <p v-if="logError" class="error-text" role="alert">{{ logError }}</p>
      <p v-else-if="!records.length" class="settings-help">还没有投递记录。</p>
      <div v-else class="mail-records"><article v-for="record in records" :key="record.id"><div><b>{{ events[record.event] || record.event }}</b><span :class="['badge', {approved: record.status !== 'failed'}]">{{ statuses[record.status] || record.status }}</span></div><p>{{ record.detail }}</p><small>{{ record.recipient }} · {{ new Date(record.created_at).toLocaleString('zh-CN', {timeZone:'Asia/Shanghai'}) }}{{ record.actor ? ` · ${record.actor}` : '' }}</small></article></div>
    </section>
  </div>
</template>
<style scoped>
.mail-column { display: grid; grid-template-columns: minmax(0, 1fr); gap: 24px; }
.mail-test { margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--line); }
.mail-records { display: grid; gap: 14px; }
.mail-records article { border: 1px solid var(--line); background: var(--console-paper); border-radius: 8px; padding: 16px; }
.mail-records article > div { display: flex; align-items: center; gap: 12px; }
.mail-records b { font-size: 13px; font-weight: 500; }
.mail-records p { font-size: 13px; line-height: 1.8; margin: 8px 0; overflow-wrap: anywhere; }
.mail-records small { font-size: 11px; color: var(--console-muted); overflow-wrap: anywhere; }
</style>
