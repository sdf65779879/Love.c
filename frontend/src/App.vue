<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import Icon from "./components/Icon.vue";
import Hero from "./components/Hero.vue";
import { links, loadSite, state } from "./store";
import { api } from "./api";
const route = useRoute();
const router = useRouter();
const open = ref(false);
const showSite = computed(() => !route.meta.admin && !route.meta.public && !!state.site);
const leaving = ref(false);
watch(
  () => state.site?.background_theme,
  theme => { document.documentElement.dataset.theme = theme || "cream"; },
  { immediate: true },
);
async function leave() {
  leaving.value = true;
  try {
    await api("/visitor/logout", { method: "POST" });
    state.site = null;
    await router.replace("/enter");
  } catch { state.toast = "退出未完成，请重试"; }
  finally { leaving.value = false; }
}
watch(
  () => route.fullPath,
  () => {
    open.value = false;
  },
);
watch(
  () => [state.site?.title, route.meta.title],
  () => {
    document.title = `${state.site?.title || "LOVE.C"} · ${String(route.meta.title || "两个人的小世界")}`;
  },
);
</script>
<template>
  <a href="#main" class="skip-link">跳到主要内容</a>
  <header v-if="showSite" class="site-header cover-header">
    <div class="header-inner">
      <RouterLink to="/" class="brand"
        ><span class="brand-mark"><Icon name="heart" :size="21" /></span
        ><span
          >{{ state.site?.logo_text || state.site?.title || "LOVE.C"
          }}<small>两个人的小世界</small></span
        ></RouterLink
      >
      <nav :class="['nav', { open }]" aria-label="主导航">
        <RouterLink to="/">首页</RouterLink
        ><RouterLink v-for="link in links" :key="link.path" :to="link.path">{{
          link.title
        }}</RouterLink>
      </nav>
      <button
        class="menu-toggle icon-button"
        :aria-expanded="open"
        aria-label="展开导航"
        @click="open = !open"
      >
        <Icon :name="open ? 'close' : 'menu'" />
      </button>
      <span class="header-note"><i /> 好好相爱，慢慢生活</span>
    </div>
  </header>
  <Hero v-if="showSite" :compact="route.path !== '/'" />
  <main id="main" tabindex="-1">
    <div v-if="!route.meta.public && state.loading && !state.site" class="status-block">
      <span class="spinner" />正在打开我们的小世界…
    </div>
    <div v-else-if="!route.meta.public && state.error && !state.site" class="status-block">
      <h1>小站暂时没有连接上</h1>
      <p role="alert">{{ state.error }}</p>
      <button class="button" @click="loadSite">重新连接</button>
    </div>
    <RouterView v-else v-slot="{ Component }"
      ><component :is="Component" :key="route.fullPath"
    /></RouterView>
  </main>
  <footer v-if="showSite" class="site-footer">
    <Icon name="heart" :size="22" />
    <p>{{ state.site?.footer_text || "把心动写进生活，把你写进余生。" }}</p>
    <div>
      © {{ new Date().getFullYear() }} {{ state.site?.title || "LOVE.C"
      }}<span>·</span><RouterLink to="/admin">管理小站</RouterLink>
      <span>·</span><button class="text-link" :disabled="leaving" @click="leave">{{ leaving ? '正在退出…' : '退出小站' }}</button>
    </div>
    <a
      v-if="state.site?.icp"
      href="https://beian.miit.gov.cn/"
      target="_blank"
      rel="noopener"
      class="icp"
      >{{ state.site.icp }}</a
    >
  </footer>
  <Transition name="toast"
    ><div v-if="state.toast" class="toast-message" role="status">
      <Icon name="check" />{{ state.toast }}
    </div></Transition
  >
</template>
