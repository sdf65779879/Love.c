<script setup lang="ts">
import { reactive } from "vue";
import { api, write } from "../api";
import { state, loadSite, notify, links } from "../store";
import CoupleAvatar from "./CoupleAvatar.vue";
import MediaField from "./MediaField.vue";

defineProps<{ about?: boolean }>();
const site = state.site!;
const basic = reactive({ title: site.title, logo_text: site.logo_text || "", subtitle: site.subtitle,
  avatar_blur: site.avatar_blur !== false, messages_enabled: site.messages_enabled });
const couple = reactive({ boy_name: site.boy_name, girl_name: site.girl_name,
  boy_qq: site.boy_qq || "", girl_qq: site.girl_qq || "", boy_avatar: site.boy_avatar,
  girl_avatar: site.girl_avatar, start_date: site.start_date.slice(0, 19) });
const cards = reactive({ cover: site.cover, footer_text: site.footer_text, icp: site.icp,
  card_titles: Object.fromEntries(links.map(link => [link.path, site.card_titles?.[link.path] || link.title])) });
const story = reactive({ about_intro: site.about_intro, about_story: site.about_story, about_future: site.about_future });
const busy = reactive<Record<string, boolean>>({});
const errors = reactive<Record<string, string>>({});
const unavailable = reactive({ boy: false, girl: false });
async function save(section: string, data: object) {
  if (busy[section]) return;
  busy[section] = true;
  errors[section] = "";
  try {
    await api("/admin/site", write("PATCH", data));
    await loadSite();
    notify("设置已保存，首页已同步更新");
  } catch (error) {
    errors[section] = (error as Error).message;
  } finally { busy[section] = false; }
}
</script>

<template>
  <form v-if="about" class="console-card settings-panel" @submit.prevent="save('about', story)">
    <h1>关于我们</h1>
    <label>小站介绍<textarea v-model="story.about_intro" required maxlength="3000" rows="4" /></label>
    <label>我们的故事<textarea v-model="story.about_story" required maxlength="5000" rows="6" /></label>
    <label>写给未来<textarea v-model="story.about_future" required maxlength="5000" rows="6" /></label>
    <p v-if="errors.about" class="error-text" role="alert">{{ errors.about }}</p>
    <div class="settings-actions"><button class="button" :disabled="busy.about">{{ busy.about ? '保存中…' : '保存关于我们' }}</button></div>
  </form>
  <div v-else class="settings-grid">
    <form class="console-card settings-panel" @submit.prevent="save('basic', basic)">
      <h1>基本设置</h1>
      <label>站点标题<input v-model="basic.title" required maxlength="80" /></label>
      <label>站点 LOGO 文字<input v-model="basic.logo_text" maxlength="80" placeholder="留空使用站点标题" /></label>
      <label>站点文案<textarea v-model="basic.subtitle" maxlength="200" rows="3" /></label>
      <label>头像背景模糊<select v-model="basic.avatar_blur"><option :value="true">开启</option><option :value="false">关闭</option></select></label>
      <label>开放留言<select v-model="basic.messages_enabled"><option :value="true">开启</option><option :value="false">关闭</option></select></label>
      <p v-if="errors.basic" class="error-text" role="alert">{{ errors.basic }}</p>
      <div class="settings-actions"><button class="button" :disabled="busy.basic">{{ busy.basic ? '保存中…' : '保存基本设置' }}</button></div>
    </form>

    <form class="console-card settings-panel" @submit.prevent="save('couple', { ...couple, start_date: couple.start_date + '+08:00' })">
      <h2>情侣配置</h2>
      <div class="couple-preview">
        <div><CoupleAvatar partner="boy" :qq="couple.boy_qq" :custom="couple.boy_avatar" :alt="couple.boy_name + '的头像'" @unavailable="unavailable.boy = $event" /><b>{{ couple.boy_name || '男主' }}</b></div>
        <span aria-hidden="true">♥</span>
        <div><CoupleAvatar partner="girl" :qq="couple.girl_qq" :custom="couple.girl_avatar" :alt="couple.girl_name + '的头像'" @unavailable="unavailable.girl = $event" /><b>{{ couple.girl_name || '女主' }}</b></div>
      </div>
      <div class="couple-fields">
        <label>男主昵称<input v-model="couple.boy_name" required maxlength="30" autocomplete="off" /></label>
        <label>女主昵称<input v-model="couple.girl_name" required maxlength="30" autocomplete="off" /></label>
        <label>男主 QQ<input v-model.trim="couple.boy_qq" inputmode="numeric" pattern="[1-9][0-9]{4,10}" maxlength="11" title="请输入 5 至 11 位 QQ 号，首位不能为 0" placeholder="输入 QQ 号获取头像" autocomplete="off" /></label>
        <label>女主 QQ<input v-model.trim="couple.girl_qq" inputmode="numeric" pattern="[1-9][0-9]{4,10}" maxlength="11" title="请输入 5 至 11 位 QQ 号，首位不能为 0" placeholder="输入 QQ 号获取头像" autocomplete="off" /></label>
      </div>
      <p class="settings-help">输入 QQ 号即可预览头像，保存后显示在首页。清空 QQ 号可恢复自定义头像。</p>
      <p class="settings-help">这两个 QQ 号对应的 @qq.com 邮箱也是小站的登录邮箱。修改号码会使现有的小站登录和验证码失效；清空双方号码后，前台将无人能够登录。</p>
      <p v-if="unavailable.boy || unavailable.girl" class="settings-help" role="status">QQ 头像暂时无法加载，已显示备用头像，可稍后重新尝试。</p>
      <label>相恋时间（北京时间）<input v-model="couple.start_date" type="datetime-local" step="1" required /></label>
      <details class="custom-avatars"><summary>自定义 / 备用头像</summary>
        <MediaField v-model="couple.boy_avatar" label="男主自定义头像" />
        <MediaField v-model="couple.girl_avatar" label="女主自定义头像" />
      </details>
      <p v-if="errors.couple" class="error-text" role="alert">{{ errors.couple }}</p>
      <div class="settings-actions"><button class="button" :disabled="busy.couple">{{ busy.couple ? '保存中…' : '保存情侣配置' }}</button></div>
    </form>

    <form class="console-card settings-panel settings-wide" @submit.prevent="save('cards', cards)">
      <h2>卡片配置 &amp; 版权配置</h2>
      <MediaField v-model="cards.cover" label="首页背景图片" />
      <div class="couple-fields"><label v-for="link in links" :key="link.path">{{ link.title }}卡片名称<input v-model="cards.card_titles[link.path]" maxlength="30" required /></label></div>
      <label>页脚文案<input v-model="cards.footer_text" maxlength="200" /></label>
      <label>备案号<input v-model="cards.icp" maxlength="100" /></label>
      <p v-if="errors.cards" class="error-text" role="alert">{{ errors.cards }}</p>
      <div class="settings-actions"><button class="button" :disabled="busy.cards">{{ busy.cards ? '保存中…' : '保存卡片与版权配置' }}</button></div>
    </form>
  </div>
</template>
