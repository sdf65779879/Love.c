<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { api, dateLabel, write, type Entry, type Page } from "../api";
import { state, notify } from "../store";
import Icon from "../components/Icon.vue";
const entries = ref<Entry[]>([]),
  page = ref(1),
  total = ref(0),
  loading = ref(false),
  error = ref(""),
  sending = ref(false),
  sendError = ref("");
const form = reactive({ name: "", content: "", website: "" });
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await api<Page>(`/content/messages?page=${page.value}`);
    entries.value.push(...result.items);
    total.value = result.total;
    page.value++;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
async function send() {
  sending.value = true;
  sendError.value = "";
  try {
    const result = await api("/messages", write("POST", form));
    form.content = "";
    notify(result.message);
  } catch (e) {
    sendError.value = (e as Error).message;
  } finally {
    sending.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div class="container page-container message-container">
    <header class="page-title">
      <p class="section-kicker">LEAVE A LITTLE LOVE</p>
      <h1>留言板</h1>
      <p>见字如面，你的祝福我们都有认真收藏。</p>
    </header>
    <form
      v-if="state.site?.messages_enabled"
      class="message-form panel"
      @submit.prevent="send"
    >
      <div class="section-row">
        <h2><Icon name="message" /> 留下一点温柔</h2>
        <span>每一句祝福，都是小小的心意</span>
      </div>
      <label
        >你的昵称<input
          v-model="form.name"
          placeholder="怎么称呼你呢？"
          maxlength="40"
          required
          autocomplete="nickname" /></label
      ><label
        >想说的话<textarea
          v-model="form.content"
          placeholder="写下祝福，或者和我们打个招呼吧…"
          maxlength="1000"
          rows="4"
          required
        /></label
      ><label class="honeypot" aria-hidden="true"
        >个人网站<input v-model="form.website" tabindex="-1" autocomplete="off"
      /></label>
      <div class="form-foot">
        <small
          >留言审核后公开，请不要填写隐私信息。<span
            >{{ form.content.length }} / 1000</span
          ></small
        ><button class="button" :disabled="sending">
          <Icon name="heart" :size="16" />{{
            sending ? "祝福寄送中…" : "送出祝福"
          }}
        </button>
      </div>
      <p v-if="sendError" class="error-text" role="alert">{{ sendError }}</p>
    </form>
    <div v-else class="panel empty-state">
      <Icon name="message" :size="30" />
      <p>留言板暂时休息中，已有的祝福仍然在这里。</p>
    </div>
    <div class="section-row message-heading">
      <h2>
        被收藏的祝福 <small>{{ total }}</small>
      </h2>
      <span>谢谢你，来过我们的小世界。</span>
    </div>
    <div class="messages-grid">
      <article
        v-for="(item, i) in entries"
        :key="item.id"
        :class="['message-card', `tone-${i % 3}`]"
      >
        <div>
          <span class="letter-avatar">{{ item.name?.slice(0, 1) }}</span>
          <h3>
            {{ item.name }}<small>{{ dateLabel(item.created_at) }}</small>
          </h3>
          <Icon name="heart" :size="16" />
        </div>
        <p class="preserve">{{ item.content }}</p>
      </article>
    </div>
    <div v-if="loading" class="status-block">
      <span class="spinner" />正在打开祝福…
    </div>
    <div v-else-if="error" class="status-block" role="alert">
      <p>{{ error }}</p>
      <button class="button secondary" @click="load">重新加载</button>
    </div>
    <div v-else-if="!entries.length" class="empty-state">
      <Icon name="message" :size="36" />
      <h2>第一份祝福，会是你的吗？</h2>
      <p>这里的每一条留言，都会被好好珍藏。</p>
    </div>
    <button
      v-if="entries.length < total && !loading && !error"
      class="button secondary load-more"
      @click="load"
    >
      看看更多祝福
    </button>
  </div>
</template>
