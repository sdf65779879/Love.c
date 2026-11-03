import { reactive } from "vue";
import { api } from "./api";

export interface Site {
  id: number;
  title: string;
  subtitle: string;
  logo_text: string;
  avatar_blur: boolean;
  card_titles: Record<string, string>;
  boy_name: string;
  boy_qq: string;
  girl_qq: string;
  girl_name: string;
  boy_avatar: string;
  girl_avatar: string;
  cover: string;
  start_date: string;
  about_intro: string;
  about_story: string;
  about_future: string;
  footer_text: string;
  icp: string;
  messages_enabled: boolean;
  source_url: string;
  stats: {
    articles: number;
    photos: number;
    wishes: number;
    completed: number;
    gifts: number;
  };
}
export const state = reactive({
  site: null as Site | null,
  error: "",
  loading: true,
  toast: "",
});
export async function loadSite() {
  state.loading = true;
  state.error = "";
  try {
    state.site = await api<Site>("/site");
  } catch (error) {
    state.error = (error as Error).message;
  } finally {
    state.loading = false;
  }
}
let toastTimer: ReturnType<typeof setTimeout>;
export function notify(message: string) {
  state.toast = message;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    state.toast = "";
  }, 4200);
}
export const links = [
  {
    path: "/moments",
    title: "点点滴滴",
    en: "OUR MOMENTS",
    desc: "有人愿意听你碎碎念，也很浪漫。",
    icon: "book",
    color: "blue",
    asset: 1,
  },
  {
    path: "/messages",
    title: "留言板",
    en: "LITTLE WISHES",
    desc: "把温柔的祝福，留在这里。",
    icon: "message",
    color: "pink",
    asset: 2,
  },
  {
    path: "/about",
    title: "关于我们",
    en: "ABOUT US",
    desc: "故事不长，刚好有你。",
    icon: "sparkles",
    color: "purple",
    asset: 3,
  },
  {
    path: "/album",
    title: "恋爱相册",
    en: "LOVE ALBUM",
    desc: "按下快门，收藏每一次心动。",
    icon: "camera",
    color: "yellow",
    asset: 4,
  },
  {
    path: "/wishlist",
    title: "恋爱清单",
    en: "OUR BUCKET LIST",
    desc: "想和你一起，把心愿慢慢实现。",
    icon: "list",
    color: "orange",
    asset: 5,
  },
  {
    path: "/gifts",
    title: "礼物墙",
    en: "GIFTS OF LOVE",
    desc: "礼物有价，偏爱无价。",
    icon: "gift",
    color: "green",
    asset: 6,
  },
];
