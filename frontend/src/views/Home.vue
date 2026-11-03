<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import Icon from "../components/Icon.vue";
import { api, dateLabel, type Page, type Entry } from "../api";
import { state, links } from "../store";
const now = ref(Date.now());
const timer = setInterval(() => {
  now.value = Date.now();
}, 1000);
onUnmounted(() => clearInterval(timer));
const elapsed = computed(() => {
  const seconds = Math.max(
    0,
    Math.floor((now.value - new Date(state.site!.start_date).getTime()) / 1000),
  );
  return [
    Math.floor(seconds / 86400),
    Math.floor(seconds / 3600) % 24,
    Math.floor(seconds / 60) % 60,
    seconds % 60,
  ];
});
const latest = ref<Entry[]>([]);
const recentError = ref("");
onMounted(async () => {
  try {
    latest.value = (await api<Page>("/content/articles?page_size=2")).items;
  } catch (e) {
    recentError.value = (e as Error).message;
  }
});
</script>
<template>
  <div class="home container">
    <section class="love-clock" aria-label="相恋计时">
      <p class="section-kicker"><span /> THE DAYS WITH YOU <span /></p>
      <h1>这是我们一起走过的</h1>
      <div class="time-digits">
        <template v-for="(value, i) in elapsed" :key="i"
          ><span class="time-part"
            ><b>{{ i === 0 ? value : String(value).padStart(2, "0") }}</b
            ><small>{{ ["天", "时", "分", "秒"][i] }}</small></span
          ><i v-if="i < 3">:</i></template
        >
      </div>
      <p class="clock-foot">
        <Icon name="heart" :size="12" />始于
        {{ dateLabel(state.site?.start_date) }}，未完待续。
      </p>
    </section>
    <section class="feature-grid" aria-label="我们的小世界">
      <RouterLink
        v-for="link in links"
        :key="link.path"
        :to="link.path"
        :class="['feature-card', link.color]"
      >
        <img
          :src="`/images/likegirl_card_${link.asset}.svg`"
          alt=""
          width="54"
          height="54"
        />
        <div>
          <small>{{ link.en }}</small>
          <h2>{{ state.site?.card_titles?.[link.path] || link.title }}</h2>
          <p>{{ link.desc }}</p>
        </div>
        <Icon name="arrow" :size="19" />
      </RouterLink>
    </section>
    <section class="home-bottom">
      <div class="recent-moments">
        <div class="section-row">
          <div>
            <p class="section-kicker">LIFE, LOVE & LITTLE THINGS</p>
            <h2>最近的小幸福<span> / </span></h2>
          </div>
          <RouterLink to="/moments" class="text-link"
            >全部故事 <Icon name="arrow" :size="16"
          /></RouterLink>
        </div>
        <p v-if="recentError" class="error-text" role="alert">
          {{ recentError }}
        </p>
        <p v-else-if="!latest.length" class="muted">
          故事正要开始，去后台写下第一篇日记吧。
        </p>
        <RouterLink
          v-for="item in latest"
          :key="item.id"
          :to="`/moments/${item.id}`"
          class="recent-item"
          ><div class="date-square">
            <b>{{ item.date?.slice(8, 10) }}</b
            ><small>{{ item.date?.slice(0, 7).replace("-", ".") }}</small>
          </div>
          <div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.excerpt }}</p>
          </div>
          <Icon name="chevron" :size="16"
        /></RouterLink>
      </div>
      <RouterLink to="/wishlist" class="quote-card"
        ><span class="quote-mark">“</span>
        <p>人间有风，有雨，有阳光，<br />还有一个很好的你。</p>
        <div>
          <span>我们的心愿进度</span
          ><b
            >{{ state.site?.stats.completed }} /
            {{ state.site?.stats.wishes }}</b
          >
        </div>
        <div class="progress-track">
          <i
            :style="{
              width: `${state.site?.stats.wishes ? (state.site.stats.completed / state.site.stats.wishes) * 100 : 0}%`,
            }"
          />
        </div>
        <small>一件一件，和你慢慢完成 <Icon name="arrow" :size="14" /></small
      ></RouterLink>
    </section>
  </div>
</template>
