<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api, dateLabel, type Entry } from "../api";
import Icon from "../components/Icon.vue";
const route = useRoute(),
  entry = ref<Entry | null>(null),
  error = ref(""),
  loading = ref(true);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    entry.value = await api<Entry>(`/articles/${route.params.id}`);
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div class="container article-container">
    <RouterLink to="/moments" class="text-link back-link"
      >← 回到点点滴滴</RouterLink
    >
    <div v-if="loading" class="status-block">故事加载中…</div>
    <div v-else-if="error" class="status-block" role="alert">
      <h1>这篇故事暂时无法打开</h1>
      <p>{{ error }}</p>
      <button class="button secondary" @click="load">重试</button>
    </div>
    <article v-else-if="entry" class="reading-panel panel">
      <p class="section-kicker">A PAGE OF OUR STORY</p>
      <h1>{{ entry.title }}</h1>
      <p class="tiny-label">
        {{ entry.author }} <span>·</span> {{ dateLabel(entry.date) }}
      </p>
      <img v-if="entry.cover" :src="entry.cover" :alt="entry.title" />
      <div class="article-content preserve">{{ entry.content }}</div>
      <div class="article-ending">
        <Icon name="heart" :size="18" />
        <p>写下来，是想把这一刻留得久一点。</p>
      </div>
    </article>
  </div>
</template>
