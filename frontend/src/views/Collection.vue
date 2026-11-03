<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api, dateLabel, type Entry, type Page } from "../api";
import Icon from "../components/Icon.vue";
import Modal from "../components/Modal.vue";
const props = defineProps<{ kind: string }>();
const entries = ref<Entry[]>([]),
  total = ref(0),
  page = ref(1),
  loading = ref(false),
  error = ref(""),
  filter = ref("all"),
  lightbox = ref<Entry | null>(null);
const meta: Record<
  string,
  { title: string; desc: string; en: string; icon: string }
> = {
  articles: {
    title: "点点滴滴",
    desc: "把日子写成诗，把你写进故事里。",
    en: "OUR MOMENTS",
    icon: "book",
  },
  photos: {
    title: "恋爱相册",
    desc: "镜头里的风景，和镜头外的你。",
    en: "LOVE ALBUM",
    icon: "camera",
  },
  wishes: {
    title: "恋爱清单",
    desc: "总有些惊奇的际遇，比方说当我遇见你。",
    en: "OUR BUCKET LIST",
    icon: "list",
  },
  gifts: {
    title: "礼物墙",
    desc: "收到的每一份礼物，都是满满的爱。",
    en: "GIFTS OF LOVE",
    icon: "gift",
  },
};
const visible = computed(() =>
  entries.value.filter(
    (e) =>
      filter.value === "all" ||
      (filter.value === "done" ? e.completed : !e.completed),
  ),
);
const completed = computed(
  () => entries.value.filter((e) => e.completed).length,
);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await api<Page>(
      `/content/${props.kind}?page=${page.value}&page_size=${props.kind === "wishes" ? 100 : 9}`,
    );
    entries.value.push(...result.items);
    total.value = result.total;
    page.value++;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div class="container page-container">
    <header class="page-title">
      <p class="section-kicker">{{ meta[kind].en }}</p>
      <h1>{{ meta[kind].title }}</h1>
      <p>{{ meta[kind].desc }}</p>
    </header>
    <template v-if="kind === 'wishes'">
      <div class="wish-summary panel">
        <Icon name="heart" :size="30" />
        <div>
          <h2>和你一起，来日方长</h2>
          <p>
            已点亮 {{ completed }} 个心愿<span v-if="entries.length < total"
              >（当前已加载 {{ entries.length }} / {{ total }}）</span
            >
          </p>
        </div>
        <strong
          >{{ completed }}<small> / {{ entries.length }}</small></strong
        >
        <div class="progress-track">
          <i
            :style="{
              width: `${entries.length ? (completed / entries.length) * 100 : 0}%`,
            }"
          />
        </div>
      </div>
      <div class="filter-tabs" aria-label="筛选心愿">
        <button
          v-for="tab in [
            { v: 'all', t: '全部心愿' },
            { v: 'done', t: '已经完成' },
            { v: 'todo', t: '未来可期' },
          ]"
          :key="tab.v"
          :class="{ active: filter === tab.v }"
          @click="filter = tab.v"
        >
          {{ tab.t }}
        </button>
      </div>
      <div class="wish-list">
        <article
          v-for="(item, i) in visible"
          :key="item.id"
          :class="['wish-row', { completed: item.completed }]"
        >
          <span class="wish-check"
            ><Icon v-if="item.completed" name="check" :size="17" /><span
              v-else
              >{{ String(i + 1).padStart(2, "0") }}</span
            ></span
          >
          <div>
            <h2>{{ item.title }}</h2>
            <small>{{
              item.completed
                ? `一起完成于 ${dateLabel(item.date) || "某个美好的日子"}`
                : "未来的某一天，要和你一起"
            }}</small>
          </div>
          <button
            v-if="item.image"
            class="icon-button"
            aria-label="查看心愿照片"
            @click="lightbox = item"
          >
            <Icon name="camera" /></button
          ><span class="wish-tag">{{
            item.completed ? "已完成" : "待实现"
          }}</span>
        </article>
      </div>
    </template>
    <div v-else :class="['collection-grid', kind]">
      <article v-for="item in entries" :key="item.id" class="collection-card">
        <RouterLink
          v-if="kind === 'articles'"
          :to="`/moments/${item.id}`"
          class="article-card-link"
          ><img
            v-if="item.cover"
            class="collection-image"
            :src="item.cover"
            :alt="item.title"
            loading="lazy" />
          <div v-else class="article-placeholder">
            <Icon name="book" :size="38" />
          </div>
          <div class="collection-copy">
            <span class="tiny-label"
              >{{ dateLabel(item.date) }} <span>·</span> {{ item.author }}</span
            >
            <h2>{{ item.title }}</h2>
            <p>{{ item.excerpt }}</p>
            <span class="text-link"
              >读读我们的故事 <Icon name="arrow" :size="15"
            /></span></div
        ></RouterLink>
        <template v-else
          ><button
            v-if="item.image"
            class="photo-button"
            :aria-label="`查看照片：${item.title}`"
            @click="lightbox = item"
          >
            <img
              class="collection-image"
              :src="item.image"
              :alt="item.title"
              loading="lazy"
            /><span><Icon name="plus" :size="26" /></span>
          </button>
          <div v-else class="gift-placeholder">
            <Icon name="gift" :size="55" />
          </div>
          <div class="collection-copy">
            <span class="tiny-label">{{ dateLabel(item.date) }}</span>
            <h2>{{ item.title }}</h2>
            <p v-if="item.location" class="location">
              <Icon name="pin" :size="14" />{{ item.location }}
            </p>
            <template v-if="kind === 'gifts'"
              ><p class="preserve">{{ item.description }}</p>
              <span class="gift-sender"
                >来自 {{ item.sender }} 的偏爱
                <Icon name="heart" :size="13" /></span
            ></template></div
        ></template>
      </article>
    </div>
    <div v-if="loading" class="status-block">
      <span class="spinner" />正在收集小幸福…
    </div>
    <div v-else-if="error" class="status-block" role="alert">
      <p>{{ error }}</p>
      <button class="button secondary" @click="load">重新加载</button>
    </div>
    <div v-else-if="!visible.length" class="empty-state">
      <Icon :name="meta[kind].icon" :size="38" />
      <h2>这里的故事，等我们一起书写</h2>
      <p>
        {{
          kind === "wishes"
            ? "换个筛选看看，或在后台添加新的心愿。"
            : "去管理小站，收藏第一份属于你们的回忆吧。"
        }}
      </p>
    </div>
    <button
      v-if="!loading && !error && entries.length < total"
      class="button secondary load-more"
      @click="load"
    >
      加载更多 <Icon name="down" :size="16" />
    </button>
    <p v-if="entries.length && entries.length >= total" class="end-note">
      故事还在继续，爱也是 <Icon name="heart" :size="12" />
    </p>
    <Modal v-if="lightbox" :title="lightbox.title" wide @close="lightbox = null"
      ><img
        class="lightbox-image"
        :src="lightbox.image"
        :alt="lightbox.title"
      />
      <p class="lightbox-caption">
        {{ dateLabel(lightbox.date) }} {{ lightbox.location }}
      </p></Modal
    >
  </div>
</template>
