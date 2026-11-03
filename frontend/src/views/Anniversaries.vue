<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { allMemories, dateLabel, type Entry } from "../api";
import Icon from "../components/Icon.vue";
import "../memories.css";
const rows = ref<Entry[]>([]), loading = ref(true), error = ref("");
const sorted = computed(() => [...rows.value].sort((a,b) => (a.days_until ?? Infinity) - (b.days_until ?? Infinity) || (a.elapsed_days || 0) - (b.elapsed_days || 0) || a.id - b.id));
let timer: ReturnType<typeof setTimeout>, active = true;
async function load() {
  clearTimeout(timer);
  loading.value = true; error.value = "";
  try { rows.value = await allMemories("anniversaries"); }
  catch(e) { error.value = (e as Error).message; }
  finally {
    loading.value = false;
    const day = 86400000;
    if(active) timer = setTimeout(load, day - ((Date.now() + 8 * 3600000) % day) + 100);
  }
}
onMounted(load);
onUnmounted(() => { active = false; clearTimeout(timer); });
</script>
<template>
  <div class="container page-container">
    <header class="page-title"><p class="section-kicker">OUR SPECIAL DAYS</p><h1>纪念日</h1><p>记住相遇的那天，也期待下一个值得庆祝的日子。</p></header>
    <p class="reminder-note">每个纪念日前两天，小站会从北京时间上午 9 点起，给你们的 QQ 邮箱各寄一封提醒。</p>
    <p v-if="loading" class="status-block">正在翻开日历…</p>
    <div v-else-if="error" class="status-block" role="alert">{{ error }}<button class="button secondary" @click="load">重试</button></div>
    <div v-else-if="!rows.length" class="panel memory-empty"><Icon name="calendar" :size="30" /><h2>哪一天对你们特别重要？</h2><p>在后台「纪念日」添加第一个日期，这里就会为你们计时。</p></div>
    <div v-else class="special-days"><article v-for="(item,i) in sorted" :key="item.id" class="panel day-card" :class="{nearest:i===0 && item.days_until!=null}">
      <p class="section-kicker"><Icon name="calendar" :size="16"/> {{ item.annual ? '每年纪念' : '特别的一天' }}</p>
      <h2>{{ item.title }}</h2>
      <div class="day-count" v-if="item.days_until===0">就是今天 <Icon name="heart"/></div>
      <div class="day-count" v-else><small>{{ item.days_until==null ? '已经过去' : '还有' }}</small> {{ item.days_until ?? item.elapsed_days }} <small>天</small></div>
      <p>纪念日期 · {{ dateLabel(item.date) }}</p>
      <p v-if="item.annual && item.next_date!==item.date">本次纪念 · {{ dateLabel(item.next_date || '') }} · 已走过 {{ item.elapsed_days }} 天</p>
      <p v-if="item.description" class="preserve">{{ item.description }}</p>
    </article></div>
  </div>
</template>
<style scoped>.reminder-note { margin:0 0 20px; text-align:center; color:#806f67; font-size:13px; line-height:1.8 }</style>
