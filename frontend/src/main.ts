import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import Home from "./views/Home.vue";
import Collection from "./views/Collection.vue";
import Messages from "./views/Messages.vue";
import About from "./views/About.vue";
import Article from "./views/Article.vue";
import Login from "./views/Login.vue";
import Admin from "./views/Admin.vue";
import NotFound from "./views/NotFound.vue";
import PrivateLogin from "./views/PrivateLogin.vue";
import { api, ApiError } from "./api";
import { loadSite, state } from "./store";
import "./style.css";

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: (_to, _from, saved) => saved || { top: 0 },
  routes: [
    { path: "/enter", component: PrivateLogin, meta: { title: "欢迎回家", public: true } },
    { path: "/", component: Home, meta: { title: "首页" } },
    {
      path: "/moments",
      component: Collection,
      props: { kind: "articles" },
      meta: { title: "点点滴滴" },
    },
    { path: "/moments/:id", component: Article, meta: { title: "我们的故事" } },
    {
      path: "/album",
      component: Collection,
      props: { kind: "photos" },
      meta: { title: "恋爱相册" },
    },
    {
      path: "/wishlist",
      component: Collection,
      props: { kind: "wishes" },
      meta: { title: "恋爱清单" },
    },
    {
      path: "/gifts",
      component: Collection,
      props: { kind: "gifts" },
      meta: { title: "礼物墙" },
    },
    { path: "/messages", component: Messages, meta: { title: "留言板" } },
    { path: "/about", component: About, meta: { title: "关于我们" } },
    {
      path: "/login",
      component: Login,
      meta: { title: "管理登录", admin: true, public: true },
    },
    {
      path: "/admin",
      component: Admin,
      meta: { title: "小站管理", admin: true },
    },
    {
      path: "/:pathMatch(.*)*",
      component: NotFound,
      meta: { title: "走错路啦" },
    },
  ],
});
router.beforeEach(async to => {
  if (to.meta.public) {
    state.site = null;
    state.error = "";
    state.loading = false;
    return;
  }
  try {
    await api(to.meta.admin ? "/auth/me" : "/visitor/me");
  } catch (error) {
    state.site = null;
    if (error instanceof ApiError && error.status === 401)
      return to.meta.admin ? "/login" : { path: "/enter", query: { next: to.fullPath } };
    return { path: to.meta.admin ? "/login" : "/enter", query: { unavailable: "1" } };
  }
  if (!state.site) await loadSite();
});
createApp(App).use(router).mount("#app");
