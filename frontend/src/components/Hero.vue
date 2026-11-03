<script setup lang="ts">
import { state } from "../store";
import Icon from "./Icon.vue";
import CoupleAvatar from "./CoupleAvatar.vue";
defineProps<{ compact?: boolean }>();
</script>
<template>
  <section
    v-if="state.site"
    :class="['hero', { compact }]"
    :style="{
      backgroundImage: `linear-gradient(90deg,rgba(45,37,31,.16),rgba(45,37,31,.03),rgba(45,37,31,.16)),url(${JSON.stringify(state.site.cover)})`,
    }"
  >
    <div class="hero-content">
      <p class="hero-eyebrow">A LITTLE WORLD, JUST FOR US</p>
      <div class="couple" :style="state.site.avatar_blur === false ? { backdropFilter: 'none' } : undefined">
        <div class="person">
          <CoupleAvatar partner="boy" :qq="state.site.boy_qq"
            :custom="state.site.boy_avatar"
            :alt="state.site.boy_name"
          /><span>{{ state.site.boy_name }}</span>
        </div>
        <div class="couple-heart">
          <Icon name="heart" :size="38" /><span>YOU & ME</span>
        </div>
        <div class="person">
          <CoupleAvatar partner="girl" :qq="state.site.girl_qq"
            :custom="state.site.girl_avatar"
            :alt="state.site.girl_name"
          /><span>{{ state.site.girl_name }}</span>
        </div>
      </div>
      <p v-if="!compact" class="hero-caption">{{ state.site.subtitle }}</p>
    </div>
    <svg
      class="waves"
      viewBox="0 0 1440 76"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path d="M0 25Q360 85 720 35T1440 25V76H0Z" fill="white" opacity=".4" />
      <path d="M0 45Q360 5 720 45T1440 35V76H0Z" fill="white" opacity=".6" />
      <path d="M0 50Q360 82 720 52T1440 53V76H0Z" fill="#fdfbf9" />
    </svg>
    <span v-if="!compact" class="hero-corner"
      >每一个有你的日子，都值得珍藏。</span
    >
  </section>
</template>
