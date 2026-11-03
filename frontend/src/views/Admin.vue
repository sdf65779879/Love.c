<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { api, ApiError, dateLabel, write, type Entry, type Page } from "../api";
import { state, loadSite, notify } from "../store";
import Icon from "../components/Icon.vue";
import Modal from "../components/Modal.vue";
import SettingsPanels from "../components/SettingsPanels.vue";
import "../admin.css";
import CityPicker from "../components/CityPicker.vue";
import MediaField from "../components/MediaField.vue";
import MailSettings from "../components/MailSettings.vue";
import { useEditorDraft } from "../useEditorDraft";
const router = useRouter();
const username = ref(""),
  ready = ref(false),
  tab = ref("settings"),
  entries = ref<Entry[]>([]),
  total = ref(0),
  page = ref(1),
  loading = ref(false),
  error = ref(""),
  busy = ref(false);
const tabs = [
  { key: "overview", name: "后台首页", icon: "home" },
  { key: "settings", name: "基本设置", icon: "list" },
  { key: "mail", name: "邮箱配置", icon: "message" },
  { key: "places", name: "走过的地方", icon: "pin" },
  { key: "articles", name: "点点滴滴", icon: "book" },
  { key: "photos", name: "恋爱相册", icon: "camera" },
  { key: "wishes", name: "恋爱清单", icon: "check" },
  { key: "anniversaries", name: "纪念日", icon: "calendar" },
  { key: "about", name: "关于页面", icon: "heart" },
  { key: "password", name: "账号安全", icon: "lock" },
];
const activeTab = computed(() => tabs.find((t) => t.key === tab.value)!);
type Field = {
  key: string;
  label: string;
  type: "text" | "textarea" | "date" | "check" | "image" | "city";
  required?: boolean;
  max?: number;
};
const fields: Record<string, Field[]> = {
  articles: [
    { key: "title", label: "故事标题", type: "text", required: true, max: 150 },
    { key: "author", label: "作者", type: "text", required: true, max: 40 },
    { key: "date", label: "记录日期", type: "date", required: true },
    { key: "cover", label: "封面图片（可选）", type: "image" },
    {
      key: "content",
      label: "故事正文（纯文本，换行保留）",
      type: "textarea",
      required: true,
      max: 50000,
    },
    { key: "published", label: "公开发布（关闭后保存为草稿）", type: "check" },
  ],
  photos: [
    { key: "title", label: "照片标题", type: "text", required: true, max: 150 },
    { key: "image", label: "照片", type: "image", required: true },
    { key: "date", label: "拍摄日期", type: "date", required: true },
    { key: "location", label: "拍摄地点（可选）", type: "text", max: 100 },
  ],
  wishes: [
    {
      key: "title",
      label: "我们的心愿",
      type: "text",
      required: true,
      max: 150,
    },
    { key: "completed", label: "我们已经一起完成啦", type: "check" },
    { key: "date", label: "完成日期（可选）", type: "date" },
    { key: "image", label: "纪念照片（可选）", type: "image" },
  ],
  places: [
    { key: "title", label: "地点名称", type: "text", required: true, max: 150 },
    { key: "city_id", label: "城市", type: "city", required: true },
    { key: "date", label: "到访日期", type: "date", required: true },
    { key: "description", label: "旅行回忆", type: "textarea", max: 3000 },
    { key: "image", label: "纪念照片（可选）", type: "image" },
  ],
  anniversaries: [
    { key: "title", label: "纪念日名称", type: "text", required: true, max: 150 },
    { key: "date", label: "纪念日期", type: "date", required: true },
    { key: "annual", label: "每年重复纪念", type: "check" },
    { key: "description", label: "关于这一天", type: "textarea", max: 3000 },
  ],
};
const editor = ref(false),
  editingId = ref<number | null>(null),
  formError = ref(""),
  deleting = ref<Entry | null>(null);
const drafts = useEditorDraft();
const { form, hasDraft, restored, persistent } = drafts;
const draftNotice = computed(() => {
  if (!hasDraft.value) return "填写时自动保存草稿，关闭后可继续填写。";
  if (!persistent.value) return "草稿暂存于当前页面，关闭弹窗后可继续；刷新页面将丢失，请尽快保存。";
  return restored.value
    ? "已恢复上次未保存的草稿。草稿仅保存在当前浏览器。"
    : "草稿已自动保存在当前浏览器，关闭或刷新后可继续填写。";
});
const passwords = reactive({ current_password: "", new_password: "" });
const passwordError = ref("");
const menuOpen = ref(false);
const counts = computed<Record<string, number | undefined>>(() => ({
  articles: state.site?.stats.articles, photos: state.site?.stats.photos,
  wishes: state.site?.stats.wishes, places: state.site?.stats.places, anniversaries: state.site?.stats.anniversaries
}));
let listRequest = 0;
async function request<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  try {
    return await api<T>(path, options);
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      notify("登录已过期，请重新登录");
      await router.replace("/login");
    }
    throw e;
  }
}
async function load() {
  const current = ++listRequest;
  if (["overview", "about", "settings", "password", "mail"].includes(tab.value)) return;
  loading.value = true;
  error.value = "";
  try {
    const result = await request<Page>(
      `/admin/content/${tab.value}?page=${page.value}&page_size=12`,
    );
    if (current !== listRequest) return;
    entries.value = result.items;
    total.value = result.total;
  } catch (e) {
    if (current === listRequest) error.value = (e as Error).message;
  } finally {
    if (current === listRequest) loading.value = false;
  }
}
async function switchTab(key: string) {
  tab.value = key;
  page.value = 1;
  entries.value = [];
  menuOpen.value = false;
  window.scrollTo(0, 0);
  await load();
}
function draftKey(id: number | null = null) {
  return `likegirl:admin-editor-draft:v1:${encodeURIComponent(username.value)}:${tab.value}:${id ?? "new"}`;
}
function openEditor(entry?: Entry) {
  editingId.value = entry?.id || null;
  formError.value = "";
  const initial: Record<string, string | boolean> = {};
  for (const field of fields[tab.value])
    initial[field.key] = entry
      ? ((entry as any)[field.key] ?? "")
      : field.type === "check"
        ? ["published", "annual"].includes(field.key)
        : field.type === "date" && field.required
          ? new Intl.DateTimeFormat("en-CA", {
              timeZone: "Asia/Shanghai",
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
            }).format(new Date())
          : "";
  if (!entry && tab.value === "articles") initial.author = state.site?.boy_name || "";
  if (tab.value === "places") initial._city_region = "";
  drafts.begin(draftKey(editingId.value), initial);
  editor.value = true;
}
function closeEditor() {
  if (!busy.value) editor.value = false;
}
function discardDraft() {
  if (busy.value || !window.confirm("放弃当前草稿？未保存的填写内容将被清除。")) return;
  drafts.clear();
  editor.value = false;
}
async function save() {
  if (busy.value) return;
  busy.value = true;
  formError.value = "";
  const data: Record<string, string | boolean | null> = { ...form };
  delete data._city_region;
  if (tab.value === "wishes" && !data.date) data.date = null;
  try {
    await request(
      `/admin/${tab.value}${editingId.value ? `/${editingId.value}` : ""}`,
      write(editingId.value ? "PUT" : "POST", data),
    );
    drafts.clear();
    editor.value = false;
    notify("这一份回忆，已好好收藏");
    await Promise.all([load(), loadSite()]);
  } catch (e) {
    formError.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}
async function remove() {
  if (!deleting.value) return;
  busy.value = true;
  try {
    await request(`/admin/${tab.value}/${deleting.value.id}`, {
      method: "DELETE",
    });
    drafts.clear(draftKey(deleting.value.id));
    deleting.value = null;
    if (entries.value.length === 1 && page.value > 1) page.value--;
    notify("内容已删除");
    await Promise.all([load(), loadSite()]);
  } catch (e) {
    error.value = (e as Error).message;
    deleting.value = null;
  } finally {
    busy.value = false;
  }
}
async function changePassword() {
  busy.value = true;
  passwordError.value = "";
  try {
    await request("/auth/password", write("POST", passwords));
    notify("密码已更新，请重新登录");
    await router.replace("/login");
  } catch (e) {
    passwordError.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}
async function logout() {
  try {
    await request("/auth/logout", { method: "POST" });
    await router.replace("/login");
  } catch (e) {
    error.value = (e as Error).message;
  }
}
onMounted(async () => {
  try {
    const user = await api<{ username: string }>("/auth/me");
    username.value = user.username;
    ready.value = true;
    menuOpen.value = false;
    await load();
  } catch (e) {
    if (e instanceof ApiError && e.status === 401)
      await router.replace("/login");
    else error.value = (e as Error).message;
  }
});
</script>
<template>
  <div class="console-shell" @keydown.esc="menuOpen = false">
    <div v-if="!ready" class="status-block">
      <p v-if="error" role="alert">{{ error }}</p>
      <span v-else class="spinner" />
    </div>
    <template v-else>
      <header class="console-bar">
        <div><button class="nav-toggle" aria-label="管理菜单" aria-controls="console-navigation" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen"><Icon :name="menuOpen ? 'close' : 'menu'"/></button><b>{{ state.site?.title }}</b><span>管理控制台</span></div>
        <div><RouterLink to="/">访问小站 ↗</RouterLink><span class="operator">{{ username }}</span><button aria-label="退出登录" @click="logout"><Icon name="logout" :size="17"/></button></div>
      </header>
      <div class="console-layout">
        <button v-if="menuOpen" class="console-menu-backdrop" aria-label="关闭管理菜单" tabindex="-1" @click="menuOpen = false" />
        <aside id="console-navigation" class="console-side" :class="{ expanded: menuOpen }">
          <nav aria-label="管理栏目"><button v-for="t in tabs" :key="t.key" :class="{ active: tab === t.key }" :aria-current="tab === t.key ? 'page' : undefined" @click="switchTab(t.key)">
            <Icon :name="t.icon" :size="17"/><span>{{ t.name }}</span><small v-if="counts[t.key] !== undefined">{{ counts[t.key] }}</small><Icon v-else name="chevron" :size="13"/>
          </button></nav>
        </aside>
        <div class="console-main">
          <div class="console-location"><span>管理中心</span> / {{ activeTab.name }}</div>
          <SettingsPanels v-if="tab === 'settings' || tab === 'about'" :key="tab" :about="tab === 'about'"/>
          <MailSettings v-else-if="tab === 'mail'" />
          <section v-else-if="tab === 'overview'" class="console-card"><h1>后台首页</h1><p class="overview-greeting">欢迎回来，{{ username }}。</p><div class="overview-links"><button v-for="t in tabs.filter(t => counts[t.key] !== undefined)" :key="t.key" @click="switchTab(t.key)"><Icon :name="t.icon"/><b>{{ counts[t.key] }}</b><span>{{ t.name }}</span></button></div></section>
          <section v-else class="console-card">
          <div class="section-row admin-section-head">
            <h2>
              {{ activeTab.name
              }}<small v-if="!['settings', 'password'].includes(tab)">{{
                total
              }}</small>
            </h2>
            <button v-if="fields[tab]" class="button" @click="openEditor()">
              <Icon name="plus" :size="17" />添加{{
                tab === "articles"
                  ? "故事"
                  : tab === "photos"
                    ? "照片"
                    : tab === "wishes"
                      ? "心愿"
                      : tab === "places" ? "地点" : "纪念日"
              }}
            </button>
          </div>
          <form
            v-if="tab === 'password'"
            class="password-form"
            @submit.prevent="changePassword"
          >
            <p class="muted">修改密码后，所有已登录会话都会失效。</p>
            <label
              >当前密码<input
                v-model="passwords.current_password"
                type="password"
                required
                autocomplete="current-password"
                maxlength="200" /></label
            ><label
              >新密码<input
                v-model="passwords.new_password"
                type="password"
                required
                minlength="12"
                maxlength="200"
                autocomplete="new-password"
                placeholder="至少 12 个字符"
            /></label>
            <p v-if="passwordError" class="error-text" role="alert">
              {{ passwordError }}
            </p>
            <button class="button" :disabled="busy">
              {{ busy ? "正在更新…" : "更新密码" }}
            </button>
          </form>
          <template v-else
            ><div v-if="error" class="error-banner" role="alert">
              {{ error }}<button class="text-link" @click="load">重试</button>
            </div>
            <div v-if="loading" class="status-block">
              <span class="spinner" />正在整理回忆…
            </div>
            <div v-else-if="!entries.length && !error" class="empty-state">
              <Icon :name="activeTab.icon" :size="35" />
              <h3>
                {{
                  "第一份回忆，等你来记录"
                }}
              </h3>
            </div>
            <div v-else class="admin-entries">
              <article
                v-for="item in entries"
                :key="item.id"
                class="admin-entry"
              >
                <img
                  v-if="item.image || item.cover"
                  :src="item.image || item.cover"
                  alt=""
                />
                <div class="admin-entry-copy">
                  <h3>
                    {{ item.title || item.name
                    }}<span
                      v-if="tab === 'articles' && !item.published"
                      class="badge"
                      >草稿</span
                    ><span
                      v-if="tab === 'wishes'"
                      :class="['badge', { approved: item.completed }]"
                      >{{ item.completed ? "已完成" : "待实现" }}</span
                    >
                  </h3>
                  <small
                    >{{ dateLabel(item.date || item.created_at) }}
                    {{
                      item.author || item.location || item.sender || ""
                    }}</small
                  >
                </div>
                <div class="entry-actions">
                  <button
                    class="icon-button"
                    :aria-label="`编辑${item.title}`"
                    @click="openEditor(item)"
                  >
                    <Icon name="edit" :size="18" /></button
                  ><button
                    class="icon-button danger"
                    :aria-label="`删除${item.title || item.name}`"
                    @click="deleting = item"
                  >
                    <Icon name="trash" :size="18" />
                  </button>
                </div>
              </article>
            </div>
            <div v-if="total > 12" class="pagination">
              <button
                class="button secondary small"
                :disabled="page === 1 || loading"
                @click="
                  page--;
                  load();
                "
              >
                上一页</button
              ><span>{{ page }} / {{ Math.ceil(total / 12) }}</span
              ><button
                class="button secondary small"
                :disabled="page * 12 >= total || loading"
                @click="
                  page++;
                  load();
                "
              >
                下一页
              </button>
            </div></template
          >
        </section>
        </div>
      </div>
      <Modal
        v-if="editor"
        :title="`${editingId ? '编辑' : '添加'} · ${activeTab.name}`"
        wide
        @close="closeEditor"
        ><form class="editor-form" @submit.prevent="save">
          <p class="editor-draft-notice" role="status">{{ draftNotice }}</p>
          <fieldset class="editor-fields" :disabled="busy">
          <template v-for="field in fields[tab]" :key="field.key"
            ><CityPicker
              v-if="field.type === 'city'"
              v-model="(form[field.key] as string)"
              v-model:region="(form._city_region as string)" /><MediaField
              v-else-if="field.type === 'image'"
              v-model="(form[field.key] as string)"
              :label="field.label"
              :required="field.required" /><label
              v-else-if="field.type === 'check'"
              class="check-label"
              ><input v-model="form[field.key]" type="checkbox" />{{
                field.label
              }}</label
            ><label v-else
              >{{ field.label
              }}<textarea
                v-if="field.type === 'textarea'"
                v-model="(form[field.key] as string)"
                :required="field.required"
                :maxlength="field.max"
                rows="8" /><input
                v-else
                v-model="form[field.key]"
                :type="field.type"
                :required="field.required"
                :maxlength="field.max" /></label
          ></template>
          </fieldset>
          <p v-if="formError" class="error-text" role="alert">
            {{ formError }}
          </p>
          <div class="modal-actions editor-actions">
            <button
              v-if="hasDraft"
              type="button"
              class="text-link discard-draft"
              :disabled="busy"
              @click="discardDraft"
            >放弃草稿</button>
            <button
              type="button"
              class="button secondary"
              :disabled="busy"
              @click="closeEditor"
            >
              暂存并关闭</button
            ><button class="button" :disabled="busy">
              {{ busy ? "正在收藏…" : "保存这份回忆" }}
            </button>
          </div>
        </form></Modal
      >
      <Modal
        v-if="deleting"
        title="删除这份记录？"
        @close="!busy && (deleting = null)"
        ><p class="delete-notice">
          「{{
            deleting.title || deleting.name
          }}」删除后无法恢复，请确认这正是你想要的操作。
        </p>
        <div class="modal-actions">
          <button
            class="button secondary"
            :disabled="busy"
            @click="deleting = null"
          >
            再想一想</button
          ><button
            class="button danger-button"
            :disabled="busy"
            @click="remove"
          >
            {{ busy ? "正在删除…" : "确认删除" }}
          </button>
        </div></Modal
      >
    </template>
  </div>
</template>
