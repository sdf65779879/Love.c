<script setup lang="ts">
import { computed, ref } from "vue";
import { state } from "../store";
import Icon from "../components/Icon.vue";
const step = ref(0);
const sections = computed(() => [
  state.site?.about_intro || "",
  state.site?.about_story || "",
  state.site?.about_future || "",
]);
const replies = ["想听听你们的故事", "那以后的日子呢？"];
</script>
<template>
  <div class="container page-container about-container">
    <header class="page-title">
      <p class="section-kicker">THE STORY OF US</p>
      <h1>关于我们</h1>
      <p>你好呀，要不要听听我们的故事？</p>
    </header>
    <section class="chat-panel panel" aria-label="与小站对话">
      <div class="chat-header">
        <Icon name="heart" />
        <div>
          <b>{{ state.site?.boy_name }} & {{ state.site?.girl_name }}</b
          ><small><i /> 我们的小世界 · 故事进行中</small>
        </div>
        <span>与你对话中</span>
      </div>
      <div class="chat-messages" aria-live="polite">
        <template v-for="(section, index) in sections" :key="index"
          ><template v-if="index <= step"
            ><div v-if="index" class="chat-reply">{{ replies[index - 1] }}</div>
            <div
              v-for="(line, n) in section.split('\n').filter(Boolean)"
              :key="n"
              class="chat-bubble"
            >
              <span v-if="n === 0" class="chat-heart"
                ><Icon name="heart" :size="15" /></span
              >{{ line }}
            </div></template
          ></template
        ><button v-if="step < 2" class="button chat-action" @click="step++">
          {{ replies[step] }} <Icon name="arrow" :size="16" />
        </button>
        <div v-else class="chat-done">
          <Icon name="heart" :size="18" />
          <p>故事未完，往后都是你。</p>
          <button class="text-link" @click="step = 0">再听一遍</button>
        </div>
      </div>
    </section>
  </div>
</template>
